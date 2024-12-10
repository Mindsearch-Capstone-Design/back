from fastapi import FastAPI, HTTPException, APIRouter
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
from datetime import datetime, timedelta
from starlette.middleware.cors import CORSMiddleware
import os
import csv
from pydantic import BaseModel


# .env 파일에서 API 키 읽기
load_dotenv()
API_KEY = os.getenv('YOUTUBE_API_KEY')

if not API_KEY:
    raise EnvironmentError("YOUTUBE_API_KEY is not set in .env file")

# YouTube API 클라이언트 생성
youtube = build('youtube', 'v3', developerKey=API_KEY)

# FastAPI 앱 초기화
app = FastAPI()


class CrawlRequest(BaseModel):
    channel_name: str
    start_date: str
    end_date: str
    platform: str


# CORS 설정
origins = ["*"]  # 모든 도메인 허용 (배포 시 제한 필요)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 생성
router = APIRouter(prefix="/api")

# 제외할 키워드 미리 지정
EXCLUDED_KEYWORDS = ["이벤트", "참가"]


# 날짜 변환 함수
def convert_to_utc(kst_date: str) -> str:
    """YYYY-MM-DD 형식의 KST 날짜를 ISO 8601 형식의 UTC로 변환"""
    try:
        kst_datetime = datetime.strptime(kst_date, "%Y-%m-%d")
        utc_datetime = kst_datetime - timedelta(hours=9)
        return utc_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise HTTPException(status_code=400, detail="날짜 형식은 YYYY-MM-DD여야 합니다.")


# 채널 ID 가져오기
def get_channel_id(query: str):
    try:
        response = youtube.search().list(
            part='snippet', q=query, type='channel', maxResults=1
        ).execute()

        if response['items']:
            return response['items'][0]['id']['channelId']
        else:
            return None
    except HttpError as e:
        raise HTTPException(status_code=500, detail=f"YouTube API Error: {e}")


# 비디오 ID와 제목 가져오기
def get_video_ids_and_titles(channel_id: str, start_date: str, end_date: str):
    video_data = []
    try:
        response = youtube.search().list(
            part='id,snippet',
            channelId=channel_id,
            maxResults=50,
            order='date',
            type='video',
            publishedAfter=start_date,
            publishedBefore=end_date,
        ).execute()

        while response:
            for item in response['items']:
                video_id = item['id']['videoId']
                video_title = item['snippet']['title']
                video_data.append({'video_id': video_id, 'title': video_title})

            if 'nextPageToken' in response:
                response = youtube.search().list(
                    part='id,snippet',
                    channelId=channel_id,
                    maxResults=50,
                    order='date',
                    type='video',
                    pageToken=response['nextPageToken'],
                    publishedAfter=start_date,
                    publishedBefore=end_date,
                ).execute()
            else:
                break
    except HttpError as e:
        raise HTTPException(status_code=500, detail=f"YouTube API Error: {e}")
    return video_data


# 댓글 가져오기
def get_comments(video_id: str, excluded_keywords=EXCLUDED_KEYWORDS):
    comments = []
    try:
        response = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            textFormat='plainText',
            maxResults=100,
        ).execute()

        while response:
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                published_at = item['snippet']['topLevelComment']['snippet']['publishedAt']

                published_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")

                if excluded_keywords and any(keyword.lower() in comment.lower() for keyword in excluded_keywords):
                    continue

                comments.append({'comment': comment, 'published_at': published_date})

            if 'nextPageToken' in response:
                response = youtube.commentThreads().list(
                    part='snippet',
                    videoId=video_id,
                    textFormat='plainText',
                    pageToken=response['nextPageToken'],
                    maxResults=100,
                ).execute()
            else:
                break
    except HttpError as e:
        if e.resp.status == 403:
            print(f"댓글이 비활성화된 비디오 ID: {video_id}")
        else:
            raise HTTPException(status_code=500, detail=f"YouTube API Error: {e}")
    return comments


# CSV 저장
def save_comments_to_csv(comments, file_name='comments.csv'):
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dataset"))
    os.makedirs(base_path, exist_ok=True)
    file_path = os.path.join(base_path, file_name)

    headers = ['published_at','comment','video_url']
    with open(file_path, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        for comment in comments:
            writer.writerow({
                'published_at': comment.get('published_at', ''),
                'comment': comment.get('comment', ''),
                'video_url': comment.get('video_url', 'N/A')
            })
    print(f"CSV 파일이 다음 경로에 저장되었습니다: {file_path}")


# API 엔드포인트 정의
@router.post("/crawl_comments")
async def api_crawl_comments(request: CrawlRequest):
    channel_name = request.channel_name
    start_date = request.start_date
    end_date = request.end_date
    platform = request.platform

    # 기존 로직 유지
    channel_id = get_channel_id(channel_name)
    if not channel_id:
        raise HTTPException(status_code=404, detail=f'Channel "{channel_name}" not found')

    start_date_utc = convert_to_utc(start_date)
    end_date_utc = convert_to_utc(end_date)

    videos = get_video_ids_and_titles(channel_id, start_date_utc, end_date_utc)
    if not videos:
        raise HTTPException(status_code=404, detail="No videos found in the given date range")

    all_comments = []
    for video in videos:
        video_id = video['video_id']
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        comments = get_comments(video_id)
        for comment in comments:
            comment['video_url'] = video_url
            comment['video_title'] = video['title']
        all_comments.extend(comments)

    save_comments_to_csv(all_comments)
    return {"message": f"Comments saved to dataset/comment.csv", "comments_count": len(all_comments)}
# FastAPI 앱에 라우터 추가
app.include_router(router)

# 앱 실행 (개발 환경)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os, csv

# .env 파일에서 API 키 읽기
load_dotenv()
API_KEY = os.getenv('YOUTUBE_API_KEY')

# YouTube API 클라이언트 생성
youtube = build('youtube', 'v3', developerKey=API_KEY)

# Flask 앱 초기화
app = Flask(__name__)

# 제외할 키워드 미리 지정
EXCLUDED_KEYWORDS = ["이벤트", "참가"]

# 한국 시간(KST)을 UTC로 변환
def convert_to_utc(kst_date):
    """YYYY-MM-DD 형식의 KST 날짜를 ISO 8601 형식의 UTC로 변환"""
    try:
        # 입력된 날짜를 KST 기준 datetime 객체로 변환
        kst_datetime = datetime.strptime(kst_date, "%Y-%m-%d")
        # UTC로 변환
        utc_datetime = kst_datetime - timedelta(hours=9)
        # ISO 8601 형식으로 변환
        return utc_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise ValueError("날짜 형식은 YYYY-MM-DD여야 합니다.")

# 검색어로 채널 ID 가져오기
def get_channel_id(query):
    try:
        response = youtube.search().list(
            part='snippet',
            q=query,
            type='channel',
            maxResults=1
        ).execute()

        if response['items']:
            channel_id = response['items'][0]['id']['channelId']
            return channel_id
        else:
            return None
    except HttpError as e:
        return None

# 비디오 ID와 제목 가져오기 (기간 필터 추가)
def get_video_ids_and_titles(channel_id, start_date=None, end_date=None):
    video_data = []
    try:
        response = youtube.search().list(
            part='id,snippet',
            channelId=channel_id,
            maxResults=50,
            order='date',
            type='video',
            publishedAfter=start_date,
            publishedBefore=end_date
        ).execute()

        while response:
            for item in response['items']:
                video_id = item['id']['videoId']
                video_title = item['snippet']['title']
                video_data.append({'video_id': video_id, 'title': video_title})

            # 다음 페이지 요청
            if 'nextPageToken' in response:
                response = youtube.search().list(
                    part='id,snippet',
                    channelId=channel_id,
                    maxResults=50,
                    order='date',
                    type='video',
                    pageToken=response['nextPageToken'],
                    publishedAfter=start_date,
                    publishedBefore=end_date
                ).execute()
            else:
                break
    except HttpError as e:
        return []

    return video_data

# 댓글 가져오기 (미리 지정된 키워드 필터링 추가)
def get_comments(video_id, excluded_keywords=EXCLUDED_KEYWORDS):
    comments = []
    try:
        response = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            textFormat='plainText',
            maxResults=100
        ).execute()

        while response:
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                published_at = item['snippet']['topLevelComment']['snippet']['publishedAt']

                # 댓글 시간 변환 (ISO 8601 -> YYYY-MM-DD)
                published_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")

                # 키워드 필터링
                if excluded_keywords:
                    if any(keyword.lower() in comment.lower() for keyword in excluded_keywords):
                        continue  # 키워드가 포함된 댓글은 건너뜀

                comments.append({'comment': comment, 'published_at': published_date})

            if 'nextPageToken' in response:
                response = youtube.commentThreads().list(
                    part='snippet',
                    videoId=video_id,
                    textFormat='plainText',
                    pageToken=response['nextPageToken'],
                    maxResults=100
                ).execute()
            else:
                break

    except HttpError as e:
        if e.resp.status == 403:
            print(f"댓글이 비활성화된 비디오 ID: {video_id}로 인한 오류 발생")
        else:
            print(f"오류 발생: {e}")

    return comments
def save_comments_to_csv(video_url, comments, file_name='comments.csv'):
    """
    댓글 데이터를 두 단계 상위 디렉터리의 dataset 폴더에 CSV 파일로 저장
    Args:
        video_url (str): 비디오 URL
        comments (list): 댓글 데이터 리스트 (딕셔너리 형태)
        file_name (str): 저장할 CSV 파일 이름
    """
    # 현재 스크립트 위치 기준으로 두 단계 상위 디렉터리의 dataset 폴더 경로 생성
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dataset"))
    
    # dataset 폴더 생성 (없으면 생성)
    os.makedirs(base_path, exist_ok=True)
    
    # 전체 파일 경로 생성
    file_path = os.path.join(base_path, file_name)
    
    # CSV 파일 헤더
    headers = ['video_url', 'comment', 'published_at']
    
    # 파일 쓰기
    with open(file_path, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        
        # 헤더 작성
        writer.writeheader()
        
        # 각 댓글 데이터를 행으로 추가
        for comment in comments:
            writer.writerow({
                'published_at': comment['published_at'],
                'comment': comment['comment'],
                'video_url': video_url
            })
    
    print(f"CSV 파일이 다음 경로에 저장되었습니다: {file_path}")

# API 엔드포인트 정의

@app.route('/get_channel_id', methods=['GET'])
def api_get_channel_id():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'query parameter is required'}), 400

    channel_id = get_channel_id(query)
    if channel_id:
        return jsonify({'channel_id': channel_id})
    else:
        return jsonify({'error': 'Channel not found'}), 404

@app.route('/get_videos', methods=['GET'])
def api_get_videos():
    channel_id = request.args.get('channel_id')
    start_date = request.args.get('start_date')  # YYYY-MM-DD 형식
    end_date = request.args.get('end_date')      # YYYY-MM-DD 형식

    if not channel_id:
        return jsonify({'error': 'channel_id parameter is required'}), 400
    if not start_date or not end_date:
        return jsonify({'error': 'start_date and end_date parameters are required'}), 400

    try:
        # KST -> UTC 변환
        start_date_utc = convert_to_utc(start_date)
        end_date_utc = convert_to_utc(end_date)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    videos = get_video_ids_and_titles(channel_id, start_date_utc, end_date_utc)
    return jsonify({'videos': videos})

@app.route('/get_comments', methods=['GET'])
def api_get_comments():
    video_id = request.args.get('video_id')
    file_name = request.args.get('file_name', 'comments.csv')  # 기본 파일 이름 설정

    if not video_id:
        return jsonify({'error': 'video_id parameter is required'}), 400

    # 비디오 URL 생성
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    # 댓글 크롤링
    comments = get_comments(video_id)

    # 댓글 CSV 저장 (두 단계 상위 디렉터리의 dataset 폴더에 저장)
    save_comments_to_csv(video_url, comments, file_name)

    return jsonify({'comments': comments, 'message': f'Comments saved to dataset/{file_name}'})


# Flask 애플리케이션 실행
if __name__ == '__main__':
    app.run(debug=True)

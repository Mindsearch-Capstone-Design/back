from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from googleapiclient.discovery import build
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import time
import os
import pandas as pd
import re
from difflib import SequenceMatcher

# .env 파일에서 환경변수 로드
load_dotenv()

INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

if not YOUTUBE_API_KEY:
    raise EnvironmentError("YOUTUBE_API_KEY is not set in .env file")

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

KST = timezone(timedelta(hours=9))
app = FastAPI()

origins = ["*"]  # 모든 도메인 허용 (배포 시 제한 필요)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/api")

# 공통 데이터 모델 정의
class CrawlRequest(BaseModel):
    account: str
    start_date: str
    end_date: str
    platform: str

# Selenium WebDriver 설정
def create_webdriver():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# CSV 저장
def save_to_csv(comments_data, filename="comments.csv"):
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dataset"))
    os.makedirs(base_path, exist_ok=True)
    file_path = os.path.join(base_path, filename)
    df = pd.DataFrame(comments_data, columns=["date", "comment", "link"])
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"크롤링 결과가 {filename} 파일에 저장되었습니다.")

# 날짜 변환
def convert_to_utc(kst_date: str) -> str:
    kst_datetime = datetime.strptime(kst_date, "%Y-%m-%d")
    utc_datetime = kst_datetime - timedelta(hours=9)
    return utc_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")

# Instagram 로그인
def instagram_login(driver, username, password):
    driver.get("https://www.instagram.com/accounts/login/")
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(10)

# Instagram 댓글 크롤링
def scrape_instagram_comments(account, start_date, end_date):
    driver = create_webdriver()
    instagram_login(driver, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)

    # 검색 버튼 클릭
    try:
        search_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'svg[aria-label="검색"]'))
        )
        search_button.click()
        print("검색 버튼 클릭 완료")
        time.sleep(2)
    except Exception as e:
        print(f"검색 버튼 클릭 실패: {e}")
        driver.quit()
        return

    # 검색 입력 필드에 채널 이름 입력
    try:
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[aria-label="입력 검색"]'))
        )
        search_input.send_keys(account)
        print(f"검색어 입력 완료: {account}")
        time.sleep(3)  # 검색 결과가 나타나기까지 잠시 대기
    except Exception as e:
        print(f"검색 입력 실패: {e}")
        driver.quit()
        return

    # 검색 결과에서 채널 선택
    try:
        # 검색 결과에서 첫 번째 링크 선택
        top_result = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.x6s0dn4 div.x9f619 a"))
        )
        top_result.click()
        print(f"채널 클릭 완료: {account}")
        time.sleep(3)
    except Exception as e:
        print(f"채널 클릭 실패: {e}")
        driver.quit()
        return

    first_post = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/p/']"))
    )
    first_post.click()
    time.sleep(3)
    comments_data = []

    # 기존 댓글 크롤링 로직
    while True:
        try:
            # 게시물 날짜 가져오기
            date_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "time.x1p4m5qa"))
            )
            post_date_str = date_element.get_attribute("datetime")
            post_date = datetime.fromisoformat(post_date_str.replace("Z", "+00:00")).astimezone(KST)
            print(f"게시물 날짜: {post_date}")

            # 날짜 범위 확인
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=KST)
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=KST)

            if post_date > end_dt:
                print("end_date 이후 게시물 - 다음 게시물로 이동")
            elif post_date < start_dt:
                print("start_date 이전 게시물 - 크롤링 종료")
                break
            else:
                print("날짜 범위 내 게시물 - 본문 해시태그 확인 진행")

                # 게시물 본문 확인
                try:
                    post_text_element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div._a9zs > h1"))
                    )
                    post_text = post_text_element.text
                    print(f"게시물 본문: {post_text}")

                    # 특정 단어 또는 해시태그 존재 여부 확인
                    if "이벤트" in post_text:
                        print("'이벤트' 단어 발견 - 다음 게시물로 이동")
                        try:
                            next_button = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located(
                                    (By.CSS_SELECTOR, 'button._abl- > div > span > svg[aria-label="다음"]'))
                            )
                            next_button.click()
                            time.sleep(3)
                            continue
                        except Exception as e:
                            print("다음 버튼이 없어 크롤링 종료:", e)
                            break
                except Exception as e:
                    print(f"본문 추출 실패: {e}")
                    continue

                # 댓글 더 보기 버튼 반복 클릭
                while True:
                    try:
                        load_more_button = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, 'button._abl- > div > svg[aria-label="댓글 더 읽어들이기"]'))
                        )
                        load_more_button.click()
                        print("더보기 버튼을 클릭했습니다.")
                        time.sleep(2)
                    except Exception:
                        print("더보기 버튼이 더이상 없습니다.")
                        break

                # 댓글 텍스트와 날짜 수집
                comment_elements = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul li"))
                )
                for comment_element in comment_elements:
                    try:
                        comment_text = comment_element.find_element(By.CSS_SELECTOR, "span._ap3a").text
                        if not comment_text.strip():
                            continue

                        comment_date_element = comment_element.find_element(By.CSS_SELECTOR, "time")
                        comment_date_str = comment_date_element.get_attribute("datetime")
                        comment_date = datetime.fromisoformat(comment_date_str.replace("Z", "+00:00")).astimezone(
                            KST)

                        comments_data.append({
                            "date": comment_date.strftime("%Y-%m-%d"),
                            "comment": comment_text,
                            "link": driver.current_url
                        })
                    except Exception as e:
                        print(f"댓글 또는 날짜 추출 실패: {e}")
                        continue

            # 다음 버튼 클릭
            try:
                next_button = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'button._abl- > div > span > svg[aria-label="다음"]'))
                )
                next_button.click()
                print("다음 버튼을 클릭했습니다.")
                time.sleep(3)
            except Exception as e:
                print("다음 버튼이 없어 크롤링 종료:", e)
                break

        except Exception as e:
            print(f"오류 발생: {e}")
            break

    driver.quit()

    save_to_csv(comments_data)
    return comments_data

# YouTube 댓글 크롤링
def scrape_youtube_comments(account, start_date, end_date):
    # 채널 ID 가져오기
    channel_id = youtube.search().list(
        part='snippet',
        q=account,
        type='channel',
        maxResults=1
    ).execute()['items'][0]['id']['channelId']

    start_date_utc = convert_to_utc(start_date)
    end_date_utc = convert_to_utc(end_date)

    # 모든 비디오 데이터 가져오기
    video_data = []
    response = youtube.search().list(
        part='id,snippet',
        channelId=channel_id,
        maxResults=50,
        order='date',
        type='video',
        publishedAfter=start_date_utc,
        publishedBefore=end_date_utc
    ).execute()
    video_data.extend(response['items'])

    while 'nextPageToken' in response:
        response = youtube.search().list(
            part='id,snippet',
            channelId=channel_id,
            maxResults=50,
            order='date',
            type='video',
            pageToken=response['nextPageToken'],
            publishedAfter=start_date_utc,
            publishedBefore=end_date_utc
        ).execute()
        video_data.extend(response['items'])

    # 댓글 크롤링
    comments_data = []
    similar_comments = []  # 유사 댓글 저장 리스트
    seen_comments = []  # 중복 및 유사 댓글 확인을 위한 리스트
    exclusion_patterns = [  # 제외할 패턴 정의
        r":",
        r"정답",
        r"이벤트"
    ]

    def is_similar(new_comment, existing_comments, threshold=0.5):
        # 기존 댓글들과 유사도 비교
        return any(SequenceMatcher(None, new_comment, existing).ratio() > threshold for existing in existing_comments)

    for video in video_data:
        video_id = video['id']['videoId']
        video_comments = []
        response = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            textFormat='plainText',
            maxResults=100
        ).execute()
        video_comments.extend(response['items'])

        while 'nextPageToken' in response:
            response = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                textFormat='plainText',
                maxResults=100,
                pageToken=response['nextPageToken']
            ).execute()
            video_comments.extend(response['items'])

        # 댓글 데이터 저장
        for item in video_comments:
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            published_at = item['snippet']['topLevelComment']['snippet']['publishedAt']

            # 1. 특정 패턴 확인 및 제외
            if any(re.search(pattern, comment) for pattern in exclusion_patterns):
                continue

            # 2. 유사도 확인
            if is_similar(comment, seen_comments):
                similar_comments.append({
                    "date": published_at.split("T")[0],
                    "comment": comment,
                    "link": f"https://www.youtube.com/watch?v={video_id}"
                })
                continue

            # 3. 댓글 저장
            comments_data.append({
                "date": published_at.split("T")[0],
                "comment": comment,
                "link": f"https://www.youtube.com/watch?v={video_id}"
            })
            seen_comments.append(comment)  # 중복 및 유사도 비교를 위해 저장

    save_to_csv(comments_data, filename="comments.csv")
    save_to_csv(similar_comments, filename="similar.csv")
    return comments_data

# API 엔드포인트
@router.post("/crawl")
async def crawl(request: CrawlRequest):
    if request.platform.lower() == "instagram":
        comments = scrape_instagram_comments(request.account, request.start_date, request.end_date)
    elif request.platform.lower() == "youtube":
        comments = scrape_youtube_comments(request.account, request.start_date, request.end_date)
    else:
        raise HTTPException(status_code=400, detail="Invalid platform. Choose either 'instagram' or 'youtube'.")
    return {"message": f"Comments saved to CSV", "comments_count": len(comments)}

app.include_router(router)
# 앱 실행 (개발 환경)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

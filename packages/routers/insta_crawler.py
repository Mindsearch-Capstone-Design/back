from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import time
import os
import pandas as pd

# .env 파일에서 환경변수 로드
load_dotenv()

# 환경변수에서 사용자 이름과 비밀번호 가져오기
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")

KST = timezone(timedelta(hours=9))
# FastAPI 애플리케이션 초기화
app = FastAPI()

# Selenium WebDriver 설정
def create_webdriver():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--headless")  # 브라우저를 표시하지 않으려면 주석 해제
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Instagram 로그인 함수
def instagram_login(driver, username, password):
    try:
        driver.get("https://www.instagram.com/accounts/login/")
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, "username")))

        # 로그인 정보 입력
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()

        # 로그인 완료 대기
        time.sleep(10)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"로그인 실패: {e}")

# Instagram 크롤링 함수
# Instagram 크롤링 함수
def scrape_comments(account, start_date, end_date):
    try:
        driver = create_webdriver()

        # Instagram 로그인
        instagram_login(driver, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)

        # 계정 페이지로 이동
        driver.get(f"https://www.instagram.com/{account}/")
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # 첫 번째 게시물 클릭
        first_post = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/p/']"))
        )
        first_post.click()
        time.sleep(3)

        comments_data = []
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

        # CSV 파일로 저장
        if comments_data:
            save_to_csv(comments_data, "comments.csv")

        return comments_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오류 발생: {e}")




def save_to_csv(comments_data, filename):

    """댓글 데이터를 CSV 파일로 저장"""
    df = pd.DataFrame(comments_data, columns=["date", "comment", "link"])
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"크롤링 결과가 {filename} 파일에 저장되었습니다.")



# API 요청 데이터 모델
class InstagramCrawlRequest(BaseModel):
    account: str
    start_date: str
    end_date: str

@app.post("/crawl_insta")
async def crawl_insta(data: InstagramCrawlRequest):
    """
    Instagram 댓글 크롤링 API
    """
    try:
        comments = scrape_comments(data.account, data.start_date, data.end_date)
        return {"success": True, "comments": comments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"크롤링 실패: {e}")

if __name__ == "__main__":
    # 테스트용 변수
    account = "lx.corp"
    start_date = "2024-10-28"
    end_date = "2024-12-11"

    print(f"Testing with account: {account}, start_date: {start_date}, end_date: {end_date}")
    comments = scrape_comments(account, start_date, end_date)
    if comments:
        print("크롤링 성공:", comments)
    else:
        print("크롤링 실패.")
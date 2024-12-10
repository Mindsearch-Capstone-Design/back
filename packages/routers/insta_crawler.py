from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
from dotenv import load_dotenv
import time
import os

# .env 파일에서 환경변수 로드
load_dotenv()

# 환경변수에서 사용자 이름과 비밀번호 가져오기
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")

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
        print("로그인 성공.")
    except Exception as e:
        print(f"로그인 실패: {e}")
        driver.quit()
        raise

# Instagram 크롤링 함수
def scrape_comments(account, start_date, end_date):
    try:
        # Selenium WebDriver 시작
        driver = create_webdriver()

        # Instagram 로그인
        instagram_login(driver, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)

        # 계정 페이지로 바로 이동
        driver.get(f"https://www.instagram.com/{account}/")
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print(f"{account} 계정 페이지 로드 완료.")

        # 기간 필터링된 게시물 수집
        filtered_links = []
        while True:
            try:
                # 스크롤하여 게시물 링크 수집
                links = driver.find_elements(By.TAG_NAME, "a")
                for link in links:
                    href = link.get_attribute("href")
                    if "/p/" in href and href not in filtered_links:
                        try:
                            # 게시물 링크로 이동
                            driver.get(href)
                            time.sleep(3)

                            # 게시물 날짜 가져오기
                            date_element = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, '//time'))
                            )
                            post_date = datetime.fromisoformat(date_element.get_attribute("datetime").split("T")[0])

                            # 기간 확인
                            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                            end_dt = datetime.strptime(end_date, "%Y-%m-%d")

                            if start_dt <= post_date <= end_dt:
                                filtered_links.append(href)
                                print(f"추가된 게시물: {href}")
                            else:
                                print(f"제외된 게시물 (기간 외): {href}")
                        except Exception as e:
                            print(f"게시물 확인 중 오류 발생: {e}")
                            continue
                # 스크롤
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
                time.sleep(2)

                # 수집 종료 조건
                if len(filtered_links) >= 50:  # 수집할 게시물 수 제한
                    break
            except Exception as e:
                print(f"스크롤 작업 중 오류 발생: {e}")
                continue

        # 댓글 크롤링
        comments_data = []
        for link in filtered_links:
            try:
                driver.get(link)
                time.sleep(3)

                # 댓글 로드
                for _ in range(5):  # 최대 5번 스크롤
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
                    time.sleep(2)

                # 댓글 텍스트 수집
                comment_elements = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul li div div div span"))
                )
                for comment in comment_elements:
                    comments_data.append({"post_url": link, "comment": comment.text})
            except Exception as e:
                print(f"댓글 크롤링 중 오류 발생: {e}")
                continue

        driver.quit()
        return comments_data

    except Exception as e:
        print(f"오류 발생: {e}")
        return None

# 메인 실행부
if __name__ == '__main__':
    # 사용자 입력 받기
    account = input("Instagram 계정 이름을 입력하세요: ")
    start_date = input("크롤링 시작 날짜 (YYYY-MM-DD): ")
    end_date = input("크롤링 종료 날짜 (YYYY-MM-DD): ")

    # 크롤링 실행
    print(f"{account} 계정의 {start_date} ~ {end_date} 기간 동안의 댓글을 크롤링합니다.")
    comments = scrape_comments(account, start_date, end_date)

    if comments:
        print("크롤링 결과:")
        for comment in comments:
            print(f"URL: {comment['post_url']}, 댓글: {comment['comment']}")
    else:
        print("크롤링 실패.")

import configparser
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os


def login(driver: webdriver.Chrome):
    login_page = "https://qulingyu25.com/login?r=https%3A%2F%2Fqulingyu25.com%2F"
    config = configparser.ConfigParser()
    username: str
    password: str

    # 讀取設定檔
    config.read("./config/config.ini")

    username = config["account"]["username"]
    password = config["account"]["password"]

    driver.get(login_page)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "user_name"))
    )

    # 輸入帳號密碼
    driver.find_element(
        By.XPATH, "/html/body/div[2]/div/div[2]/div[1]/div/form/div[1]/input"
    ).send_keys(username)

    time.sleep(1.5)

    driver.find_element(
        By.XPATH, "/html/body/div[2]/div/div[2]/div[1]/div/form/div[3]/input"
    ).send_keys(password)

    time.sleep(1.5)

    # 點擊登入按鈕
    driver.find_element(
        By.XPATH, "/html/body/div[2]/div/div[2]/div[1]/div/form/button"
    ).click()


def main():
    main_page: str = "https://qulingyu25.com/wanghong/page"
    opt = webdriver.ChromeOptions()
    opt.add_argument("--headless=new")
    driver = webdriver.Chrome(options=opt)

    print("等待登入中...")
    login(driver)
    time.sleep(1.5)
    print("登入完成")

    page_count = get_page_count()
    if page_count == 0:
        return

    image_links, titles = scrape_pages(driver, main_page, page_count)
    download_images(driver, image_links, titles)
    print("下載完成！")


def get_page_count() -> int:
    try:
        return int(input("請選擇要下載幾頁："))
    except ValueError:
        print("請輸入數字")
        return 0


def scrape_pages(driver, main_page: str, page_count: int) -> tuple[list[str], list[str]]:
    image_links = []
    titles = []

    for page in range(page_count):
        driver.get(main_page + f"/{page}")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.thumb-srcbox"))
        )
        images = driver.find_elements(By.CSS_SELECTOR, "a.thumb-srcbox")

        for image in images:
            title = image.find_element(By.TAG_NAME, "img").get_attribute("alt")
            link = image.get_attribute("href")
            titles.append(title)
            image_links.append(link)

        print(image_links)
        print(titles)

    return image_links, titles


def download_images(driver, image_links: list[str], titles: list[str]):
    for index in range(len(image_links)):
        title = titles[index]
        dir_name = f"images/{title}"
        if os.path.exists(dir_name):
            print(f"{title} 已存在，跳過下載...")
            continue

        print(f"正在下載 {title}")
        create_directory(dir_name)
        download_image(driver, image_links[index], dir_name)


def create_directory(dir_name: str):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def download_image(driver, image_link: str, dir_name: str):
    driver.get(image_link)
    driver.implicitly_wait(10)

    scroll_and_wait(driver)

    image_page_content = driver.page_source
    soup = BeautifulSoup(image_page_content, "html.parser")
    content = soup.find(class_="content")
    images = content.find_all("img")

    save_images(driver, images, dir_name)


def scroll_and_wait(driver):
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "footer"))
        )


def save_images(driver, images, dir_name: str):
    allow = ["jpg", "png", "jpeg"]
    for img in images:
        src = img.get("data-src")
        if src and any(ext in src.lower() for ext in allow):
            file_name = src.split("/")[-1]
            if file_name == "logo.png":
                continue
            file_path = f"{dir_name}/{file_name}"
            driver.get(src)
            with open(file_path, "wb") as file:
                file.write(
                    driver.find_element(by=By.XPATH, value="/html/body/img").screenshot_as_png
                )
            time.sleep(1.5)


if __name__ == "__main__":
    main()

import configparser
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os


def login(driver: webdriver.Chrome):
    login_page = "https://qulingyu30.com/login?r=https://qulingyu30.com/"
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
    main_page: str = "https://qulingyu30.com/"
    opt = webdriver.ChromeOptions()
    opt.add_argument("--headless=new")
    driver = webdriver.Chrome(options=opt)

    print("等待登入中...")
    login(driver)
    time.sleep(1.5)
    print("登入完成")

    page_link = get_page_link()
    if not page_link:
        return

    page_count = get_page_count()
    if page_count == 0:
        return

    image_links, titles = scrape_pages(driver, page_link, page_count)
    print(f"➡️ 導入的分頁連結：{titles}")
    download_images(driver, image_links, titles)
    print("下載完成！")

def get_page_link() -> str:
    print("請選擇要下載的分頁：")
    print("1. 唯美寫真")
    print("2. 動漫博主")
    print("3. 絕對領域")
    print("4. 趣澀圖 需要開通會員")
    print("5. 趣視頻 需要開通會員")
    print("6. 老司機 需要開通會員")

    try:
        choice = int(input("輸入編號："))
    except ValueError:
        print("請輸入有效的數字")
        return ""

    page_links = {
        1: "https://qulingyu30.com/taotu",
        2: "https://qulingyu30.com/wanghong",
        3: "https://qulingyu30.com/lingyu",
        4: "https://qulingyu30.com/laosiji",
        5: "https://qulingyu30.com/qushipin",
        6: "https://qulingyu30.com/qiumingshan",
    }

    return page_links.get(choice, "")

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
        if page == 0:
            url = f"{main_page}/"  # 第一頁
        else:
            url = f"{main_page}/page/{page + 1}"  # 第二頁開始從 /2、/3...

        print(f"[INFO] 正在載入第 {page + 1} 頁：{url}")

        driver.get(url)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.thumb-srcbox"))
            )
            print(f"[INFO] 第 {page + 1} 頁載入完成，開始擷取圖片資料")
        except Exception as e:
            print(f"[ERROR] 第 {page + 1} 頁等待元素失敗: {e}")
            continue

        images = driver.find_elements(By.CSS_SELECTOR, "a.thumb-srcbox")
        print(f"[INFO] 發現 {len(images)} 個圖片元素")

        for i, image in enumerate(images):
            try:
                img_tag = image.find_element(By.TAG_NAME, "img")
                title = img_tag.get_attribute("alt")
                link = image.get_attribute("href")
                titles.append(title)
                image_links.append(link)
                print(f"[DEBUG] 第 {i + 1} 張：{title} -> {link}")
            except Exception as e:
                print(f"[WARNING] 擷取第 {i + 1} 張圖片時發生錯誤：{e}")
                continue

    print(f"[INFO] 所有頁面處理完成，總共取得 {len(image_links)} 筆圖片連結")
    return image_links, titles


def download_images(driver, image_links: list[str], titles: list[str]):
    for index in range(len(image_links)):
        title = titles[index]
        dir_name = f"images/{title}"
        if os.path.exists(dir_name):
            print(f"[INFO] {title} 已存在，跳過下載...")
            continue

        print(f"[INFO] 正在下載：{title}")
        create_directory(dir_name)
        download_image(driver, image_links[index], dir_name)


def create_directory(dir_name: str):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
        print(f"[INFO] 建立資料夾：{dir_name}")
    else:
        print(f"[INFO] 資料夾已存在：{dir_name}")


def download_image(driver, image_link: str, dir_name: str):
    print(f"[INFO] 開啟圖片頁面：{image_link}")
    driver.get(image_link)
    driver.implicitly_wait(10)

    scroll_and_wait(driver)

    print(f"[INFO] 擷取圖片頁面 HTML")
    image_page_content = driver.page_source
    soup = BeautifulSoup(image_page_content, "html.parser")
    content = soup.find(class_="content")
    if not content:
        print(f"[WARNING] 無法找到圖片內容區塊：{image_link}")
        return

    images = content.find_all("img")
    print(f"[INFO] 發現 {len(images)} 張圖片，下載中...")
    save_images(driver, images, dir_name)


def scroll_and_wait(driver):
    for i in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "footer"))
            )
        except Exception as e:
            print(f"[WARNING] 頁尾載入失敗：{e}")


def save_images(driver, images, dir_name: str):
    allow = ["jpg", "png", "jpeg"]
    for i, img in enumerate(images):
        src = img.get("data-src")
        if src and any(ext in src.lower() for ext in allow):
            file_name = src.split("/")[-1]
            if file_name == "logo.png":
                print(f"[DEBUG] 跳過 logo.png")
                continue

            file_path = f"{dir_name}/{file_name}"
            # print(f"[INFO] 正在下載第 {i + 1} 張圖片：{file_name}")

            try:
                driver.get(src)
                with open(file_path, "wb") as file:
                    file.write(
                        driver.find_element(by=By.XPATH, value="/html/body/img").screenshot_as_png
                    )
                # print(f"[INFO] 已儲存圖片：{file_path}")
                time.sleep(1.5)
            except Exception as e:
                print(f"[ERROR] 下載圖片 {src} 失敗：{e}")


if __name__ == "__main__":
    main()

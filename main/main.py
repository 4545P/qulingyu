# 導入所需模組
import configparser
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import platform


# 取得桌面路徑，根據作業系統決定正確位置
def get_desktop_path():
    home = os.path.expanduser("~")
    system = platform.system()
    if system == "Windows":
        return os.path.join(home, "Desktop")
    elif system == "Darwin":  # macOS
        return os.path.join(home, "Desktop")
    else:
        return os.path.join(home, "Desktop")  # Linux 預設也這樣寫


# 使用帳號密碼登入網站
def login(driver: webdriver.Chrome, config: configparser.ConfigParser):
    # 從設定檔讀取帳密與主頁網址
    username = config["account"]["username"]
    password = config["account"]["password"]
    main_page = config["site"]["url"]
    login_page = f"{main_page}login?r={main_page}"

    # 開啟登入頁
    driver.get(login_page)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "user_name"))
    )

    # 輸入帳號
    driver.find_element(
        By.XPATH, "/html/body/div[2]/div/div[2]/div[1]/div/form/div[1]/input"
    ).send_keys(username)

    time.sleep(1.5)

    # 輸入密碼
    driver.find_element(
        By.XPATH, "/html/body/div[2]/div/div[2]/div[1]/div/form/div[3]/input"
    ).send_keys(password)

    time.sleep(1.5)

    # 點擊登入按鈕
    driver.find_element(
        By.XPATH, "/html/body/div[2]/div/div[2]/div[1]/div/form/button"
    ).click()

    return main_page  # 回傳主頁網址供後續使用


# 主程式
def main():
    # 取得桌面上 quImages 的資料夾路徑
    desktop_base = os.path.join(get_desktop_path(), "quImages")

    # 若資料夾不存在則建立
    if not os.path.exists(desktop_base):
        os.makedirs(desktop_base)
        print(f"[INFO] 建立資料夾：{desktop_base}")

    # ✅ 讀取設定檔
    config = configparser.ConfigParser()
    config.read("./config/config.ini")  # 確保 config.ini 放在正確位置

    # 啟用 Chrome 瀏覽器（無頭模式）
    opt = webdriver.ChromeOptions()
    opt.add_argument("--headless=new")
    driver = webdriver.Chrome(options=opt)

    print("等待登入中...")
    main_page = login(driver, config)  # ✅ 登入並取得 main_page
    time.sleep(1.5)
    print("登入完成")

    # 讓使用者選擇分頁類型
    page_link = get_page_link(main_page)
    if not page_link:
        return

    # 讓使用者輸入要下載的頁數
    page_count = get_page_count()
    if page_count == 0:
        return

    # 擷取所有分頁的圖片連結與標題
    image_links, titles = scrape_pages(driver, page_link, page_count)
    print(f"➡️ 導入的分頁連結：{titles}")

    # 下載圖片
    download_images(driver, image_links, titles, desktop_base)
    print("下載完成！")


# 提供選單讓使用者選擇要下載的頁面
def get_page_link(main_page: str) -> str:
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
        1: f"{main_page}taotu",
        2: f"{main_page}wanghong",
        3: f"{main_page}lingyu",
        4: f"{main_page}laosiji",
        5: f"{main_page}qushipin",
        6: f"{main_page}qiumingshan",
    }

    return page_links.get(choice, "")


# 讓使用者輸入要爬取幾頁
def get_page_count() -> int:
    try:
        return int(input("請選擇要下載幾頁："))
    except ValueError:
        print("請輸入數字")
        return 0


# 爬取所有指定頁數中的圖片頁面連結與標題
def scrape_pages(driver, main_page: str, page_count: int) -> tuple[list[str], list[str]]:
    image_links = []
    titles = []

    for page in range(page_count):
        url = f"{main_page}/" if page == 0 else f"{main_page}/page/{page + 1}"

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

        # 擷取每張圖的標題與連結
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


# 下載圖片頁面中的所有圖片
def download_images(driver, image_links: list[str], titles: list[str], base_dir: str):
    for index in range(len(image_links)):
        title = titles[index]
        dir_name = os.path.join(base_dir, title)
        if os.path.exists(dir_name):
            print(f"[INFO] {title} 已存在，跳過下載...")
            continue

        print(f"[INFO] 正在下載：{title}")
        create_directory(dir_name)
        download_image(driver, image_links[index], dir_name)


# 建立圖片資料夾
def create_directory(dir_name: str):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
        print(f"[INFO] 建立資料夾：{dir_name}")
    else:
        print(f"[INFO] 資料夾已存在：{dir_name}")


# 前往單一圖片頁，擷取圖檔並儲存
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


# 模擬捲動頁面到底部
def scroll_and_wait(driver):
    for i in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "footer"))
            )
        except Exception as e:
            print(f"[WARNING] 頁尾載入失敗：{e}")


# 實際下載圖片並以螢幕擷圖方式儲存
def save_images(driver, images, dir_name: str):
    allow = ["jpg", "png", "jpeg"]
    for i, img in enumerate(images):
        src = img.get("data-src")
        if src and any(ext in src.lower() for ext in allow):
            file_name = src.split("/")[-1]
            if file_name == "logo.png":
                print(f"[DEBUG] 跳過 logo.png")
                continue

            file_path = os.path.join(dir_name, file_name)

            try:
                driver.get(src)
                # 透過 Selenium 的 screenshot_as_png 擷取圖片畫面
                with open(file_path, "wb") as file:
                    file.write(
                        driver.find_element(by=By.XPATH, value="/html/body/img").screenshot_as_png
                    )
                time.sleep(1.5)
            except Exception as e:
                print(f"[ERROR] 下載圖片 {src} 失敗：{e}")


# 執行程式
if __name__ == "__main__":
    main()

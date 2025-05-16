# 導入所需模組
import configparser
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import glob


# ----------- 1. 實用工具方法 -----------

def get_desktop_path():
    """
    功能：取得使用者桌面路徑
    傳入參數：無
    回傳內容：字串，桌面路徑
    """
    home = os.path.expanduser("~")
    return os.path.join(home, "Desktop")


def create_directory(dir_name: str):
    """
    功能：建立指定名稱的資料夾（若不存在則建立）
    傳入參數：
        dir_name (str): 資料夾名稱或路徑
    回傳內容：無
    """
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def wait_for_downloads(download_dir, stable_time=5):
    """
    無限制等待直到 .crdownload 消失且 .7z 檔案大小穩定
    """
    print("[INFO] 等待下載完成（無時間限制）...")
    prev_size = 0
    stable_counter = 0
    start_time = time.time()

    while True:
        cr_files = glob.glob(os.path.join(download_dir, "*.crdownload"))
        z_files = glob.glob(os.path.join(download_dir, "*.7z"))

        elapsed = int(time.time() - start_time)
        if cr_files:
            if elapsed % 60 == 0:
                print("[DEBUG] 發現 .crdownload 檔案，等待中...")
            stable_counter = 0

        elif z_files:
            latest_file = max(z_files, key=os.path.getmtime)
            size = os.path.getsize(latest_file)

            if size == prev_size:
                stable_counter += 1
                if stable_counter >= stable_time:
                    print(f"[INFO] 下載已完成：{os.path.basename(latest_file)}")
                    return
            else:
                prev_size = size
                stable_counter = 0

        else:
            stable_counter = 0

        time.sleep(1)


# ----------- 2. 登入與身份驗證 -----------

def login(driver: webdriver.Chrome, config: configparser.ConfigParser):
    """
    功能：透過帳號密碼登入指定網站，並返回主頁網址
    傳入參數：
        driver (webdriver.Chrome): Selenium WebDriver 物件
        config (configparser.ConfigParser): 配置檔物件，包含帳號密碼與網站資訊
    回傳內容：
        main_page (str): 登入後的主頁網址
    """
    username = config["account"]["username"]
    password = config["account"]["password"]
    main_page = config["site"]["url"]
    login_page = f"{main_page}login?r={main_page}"

    driver.get(login_page)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "user_name")))
    driver.find_element(By.XPATH, "/html/body/div[2]/div/div[2]/div[1]/div/form/div[1]/input").send_keys(username)
    time.sleep(1.5)
    driver.find_element(By.XPATH, "/html/body/div[2]/div/div[2]/div[1]/div/form/div[3]/input").send_keys(password)
    time.sleep(1.5)
    driver.find_element(By.XPATH, "/html/body/div[2]/div/div[2]/div[1]/div/form/button").click()
    return main_page


def check_membership(driver) -> bool:
    """
    功能：判斷當前登入帳號是否為VIP會員
    傳入參數：
        driver (webdriver.Chrome): Selenium WebDriver 物件
    回傳內容：
        bool: True表示VIP會員，False表示非VIP會員
    """
    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "i.vip_icon img")))
        imgs = driver.find_elements(By.CSS_SELECTOR, "i.vip_icon img")
        for img in imgs:
            src = img.get_attribute("src")
            if "vip-three.svg" in src:
                print("[INFO] 帳號是vip會員")
                return True
            if "vip_no.svg" in src:
                print("[INFO] 帳號是非vip會員")
                return False
        print("[WARN] 無法判斷會員狀態，視為非會員")
        return False
    except Exception as e:
        print(f"[ERROR] 判斷會員狀態失敗：{e}")
        return False


# ----------- 3. 使用者互動 -----------

def get_page_link(main_page: str, is_member: bool) -> str:
    """
    功能：讓使用者選擇欲下載的分頁，並回傳對應URL
    傳入參數：
        main_page (str): 主頁網址
        is_member (bool): 是否為VIP會員
    回傳內容：
        str: 選擇分頁的完整網址，若選擇離開則回傳空字串
    """
    while True:
        print("請選擇要下載的分頁：")
        print("1. 唯美寫真")
        print("2. 動漫博主")
        print("3. 絕對領域")
        print("4. 趣澀圖（需要vip會員）")
        print("5. 趣視頻（需要vip會員）")
        print("6. 老司機（需要vip會員）")
        print("0. 離開程式")

        try:
            choice = int(input("輸入編號："))
        except ValueError:
            print("請輸入有效的數字")
            continue

        if choice == 0:
            return ""

        if choice in [4, 5, 6] and not is_member:
            print("\u274c 此分頁需要會員才能下載，請重新選擇。")
            continue

        page_links = {
            1: f"{main_page}taotu",
            2: f"{main_page}wanghong",
            3: f"{main_page}lingyu",
            4: f"{main_page}laosiji",
            5: f"{main_page}qushipin",
            6: f"{main_page}qiumingshan",
        }

        return page_links.get(choice, "")


def get_page_count(mode: str) -> int:
    """
    功能：根據下載模式，讓使用者輸入欲下載的頁數或筆數
    傳入參數：
        mode (str): 下載模式，"resource"代表資源下載，"image"代表圖片下載
    回傳內容：
        int: 輸入的頁數或筆數，若輸入錯誤則回傳0
    """
    try:
        return int(input(f"請輸入要下載的{'筆數' if mode == 'resource' else '頁數'}："))
    except ValueError:
        print("請輸入數字")
        return 0


# ----------- 4. 資料擷取與處理 -----------

def scrape_pages(driver, main_page: str, page_count: int, mode: str) -> tuple[list[str], list[str]]:
    """
    功能：根據下載模式擷取指定頁數或筆數的圖片連結與標題
    傳入參數：
        driver (webdriver.Chrome): Selenium WebDriver 物件
        main_page (str): 分頁網址
        page_count (int): 要擷取的頁數或筆數
        mode (str): 下載模式，"resource"或"image"
    回傳內容：
        tuple: (圖片連結列表, 標題列表)

    注意：
        - 資源下載模式(resource)只載入首頁，擷取指定數量的資源連結。
        - 圖片下載模式(image)會依頁數逐頁擷取圖片資料。
    """
    image_links, titles = [], []

    if mode == "resource":
        # 僅載入首頁，抓取指定數量的資源連結
        url = f"{main_page}/"
        print(f"[INFO] 資源下載模式：正在載入首頁：{url}")
        driver.get(url)

        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.thumb-srcbox")))
        except Exception as e:
            print(f"[ERROR] 資源首頁載入失敗: {e}")
            return image_links, titles

        images = driver.find_elements(By.CSS_SELECTOR, "a.thumb-srcbox")
        print(f"[INFO] 共找到 {len(images)} 筆資源，準備擷取前 {page_count} 筆")

        for i, image in enumerate(images[:page_count]):
            try:
                img_tag = image.find_element(By.TAG_NAME, "img")
                titles.append(img_tag.get_attribute("alt"))
                image_links.append(image.get_attribute("href"))
            except Exception as e:
                print(f"[WARNING] 擷取第 {i+1} 筆資源失敗：{e}")

    else:  # 圖片下載模式，按頁數處理
        for page in range(page_count):
            url = f"{main_page}/" if page == 0 else f"{main_page}/page/{page + 1}"
            print(f"[INFO] 正在載入第 {page + 1} 頁：{url}")
            driver.get(url)

            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.thumb-srcbox")))
            except Exception as e:
                print(f"[ERROR] 第 {page + 1} 頁等待元素失敗: {e}")
                continue

            images = driver.find_elements(By.CSS_SELECTOR, "a.thumb-srcbox")
            print(f"[INFO] 發現 {len(images)} 張圖片")
            for image in images:
                try:
                    img_tag = image.find_element(By.TAG_NAME, "img")
                    titles.append(img_tag.get_attribute("alt"))
                    image_links.append(image.get_attribute("href"))
                except Exception as e:
                    print(f"[WARNING] 擷取圖片失敗：{e}")

    return image_links, titles


def get_image_links(driver, main_page, is_member, mode: str):
    """
    功能：整合分頁選擇與資料擷取流程，回傳圖片連結與標題列表
    傳入參數：
        driver (webdriver.Chrome): Selenium WebDriver 物件
        main_page (str): 主頁網址
        is_member (bool): 是否為VIP會員
        mode (str): 下載模式，"resource"或"image"
    回傳內容：
        tuple: (圖片連結列表, 標題列表)
    """
    page_link = get_page_link(main_page, is_member)
    if not page_link:
        return [], []
    page_count = get_page_count(mode)
    if page_count == 0:
        return [], []
    return scrape_pages(driver, page_link, page_count, mode)


# ----------- 5. 下載邏輯 -----------

def download_images(driver, image_links: list[str], titles: list[str], base_dir: str, mode: str):
    """
    功能：根據下載模式，執行資源或圖片的下載流程
    傳入參數：
        driver (webdriver.Chrome): Selenium WebDriver 物件
        image_links (list[str]): 圖片或資源連結列表
        titles (list[str]): 對應標題列表
        base_dir (str): 下載主資料夾路徑
        mode (str): 下載模式，"resource"或"image"
    回傳內容：無
    """
    for title, link in zip(titles, image_links):
        dir_name = os.path.join(base_dir, title)
        if os.path.exists(dir_name):
            print(f"[INFO] {title} 已存在，跳過下載...")
            continue

        print(f"[INFO] 正在下載：{title}")
        if mode == "resource":
            # 資源下載模式，不需建立資料夾，直接執行資源下載流程
            download_resource(driver, link)
        elif mode == "image":
            # 圖片下載模式，為每個標題建立資料夾，並下載圖片
            create_directory(dir_name)
            download_image(driver, link, dir_name)
        else:
            print(f"[ERROR] 不明的下載模式：{mode}")


def download_resource(driver, image_link: str):
    """
    功能：執行資源下載流程，包含點擊下載觸發器、輸入提取碼及點擊下載按鈕
    傳入參數：
        driver (webdriver.Chrome): Selenium WebDriver 物件
        image_link (str): 資源頁面連結
    回傳內容：無
    """
    print(f"[INFO] 開啟資源頁面：{image_link}")
    driver.get(image_link)
    try:
        download_trigger = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//em[text()="下载资源"]'))
        )
        download_trigger.click()
        time.sleep(1.5)  # 等待資源連結載入
    except Exception as e:
        print(f"[ERROR] 找不到或無法點擊下載觸發器：{e}")
        return

    # 取得提取碼
    try:
        down_meta = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.down_meta_dec"))
        )
        text = down_meta.text
        password = text.split("提取码：")[-1].strip()
        print(f"[INFO] 取得提取碼：{password}")
    except Exception as e:
        print(f"[ERROR] 無法取得提取碼：{e}")
        return

    # 點擊資源一下載按鈕
    try:
        download_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.Mypassdown"))
        )
        download_button.click()
    except Exception as e:
        print(f"[ERROR] 找不到或無法點擊資源一下載：{e}")
        return

    # 點擊第一次彈窗「確定」
    click_confirm_fallback(driver)

    # 等 2 秒，再點第二次彈窗「確定」
    time.sleep(2)
    click_confirm_fallback(driver)

    # 等待新分頁出現並切換
    WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
    driver.switch_to.window(driver.window_handles[-1])
    print(f"[INFO] 新分頁出現後目前頁面URL: {driver.current_url}")

    # 輸入密碼並執行後續操作
    try:
        password_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
        )
        password_input.clear()
        password_input.send_keys(password)  # 使用前面擷取的密碼變數

        # 點擊繼續按鈕
        continue_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='繼續']"))
        )
        continue_button.click()

        time.sleep(1)

        # 點擊下載按鈕
        download_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='下載']]"))
        )
        download_button.click()

        # 等待下載完成
        download_dir = os.path.join(get_desktop_path(), "quImages", "downloads")
        wait_for_downloads(download_dir)

    except Exception as e:
        print(f"[ERROR] 資源下載流程出錯：{e}")


def download_image(driver, image_link: str, dir_name: str):
    """
    功能：進入單一圖片頁面，擷取所有圖片並儲存
    傳入參數：
        driver (webdriver.Chrome): Selenium WebDriver 物件
        image_link (str): 單一圖片頁面連結
        dir_name (str): 圖片儲存資料夾路徑
    回傳內容：無
    """
    driver.get(image_link)
    driver.implicitly_wait(10)
    scroll_and_wait(driver)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    content = soup.find(class_="content")
    if not content:
        print(f"[WARNING] 無法找到圖片內容：{image_link}")
        return
    images = content.find_all("img")
    save_images(driver, images, dir_name)


def save_images(driver, images, dir_name: str):
    """
    功能：將擷取到的圖片連結下載並存檔
    傳入參數：
        driver (webdriver.Chrome): Selenium WebDriver 物件
        images (list): BeautifulSoup擷取的img標籤列表
        dir_name (str): 圖片儲存資料夾路徑
    回傳內容：無
    """
    for img in images:
        src = img.get("data-src")
        if src and any(ext in src.lower() for ext in ["jpg", "png", "jpeg"]):
            file_name = src.split("/")[-1]
            if file_name == "logo.png":
                continue
            file_path = os.path.join(dir_name, file_name)
            try:
                driver.get(src)
                with open(file_path, "wb") as file:
                    file.write(driver.find_element(By.XPATH, "/html/body/img").screenshot_as_png)
                time.sleep(1.5)
            except Exception as e:
                print(f"[ERROR] 下載圖片失敗：{e}")


# ----------- 6. 輔助功能 -----------

def scroll_and_wait(driver):
    """
    功能：將網頁捲動到底部並等待頁面元素載入，常用於動態載入內容
    傳入參數：
        driver (webdriver.Chrome): Selenium WebDriver 物件
    回傳內容：無
    """
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "footer")))
        except Exception as e:
            print(f"出錯：{e}")


def click_confirm_fallback(driver):
    """
    功能：嘗試點擊彈窗中的「確定」按鈕，先嘗試sgBtn.ok，失敗則嘗試clsBtn
    傳入參數：
        driver (webdriver.Chrome): Selenium WebDriver 物件
    回傳內容：無
    """
    try:
        btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.sgBtn.ok"))
        )
        driver.execute_script("arguments[0].click();", btn)
        print("[INFO] ✅ 已點擊 sgBtn.ok")
    except Exception as e:
        print(f"[WARN] sgBtn.ok 點擊失敗，改用 clsBtn：{e}")
        try:
            close_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.clsBtn"))
            )
            driver.execute_script("arguments[0].click();", close_btn)
            print("[INFO] ✅ 已點擊 clsBtn")
        except Exception as e2:
            print(f"[ERROR] clsBtn 點擊也失敗：{e2}")


# ----------- 7. 主流程 -----------

def main():
    """
    功能：程式主流程
        1. 建立下載資料夾
        2. 讀取設定檔
        3. 啟動瀏覽器並登入
        4. 判斷會員身份
        5. 根據會員身份與使用者選擇決定下載模式
        6. 擷取下載資料並執行下載
    傳入參數：無
    回傳內容：無
    """
    desktop_base = os.path.join(get_desktop_path(), "quImages")
    create_directory(desktop_base)
    create_directory(os.path.join(desktop_base, "downloads"))

    config = configparser.ConfigParser()
    config.read("./config/config.ini")

    opt = webdriver.ChromeOptions()
    # 設定Chrome下載資料夾
    prefs = {
        "download.default_directory": os.path.join(get_desktop_path(), "quImages", "downloads"),
        "download.prompt_for_download": False,
        "directory_upgrade": True
    }
    opt.add_experimental_option("prefs", prefs)
    opt.add_argument("--headless=new")
    driver = webdriver.Chrome(options=opt)

    try:
        # 登入流程
        print("等待登入中...")
        main_page = login(driver, config)
        time.sleep(1.5)
        print("登入完成")

        # 判斷會員身份
        is_member = check_membership(driver)

        # 非會員只能下載圖片
        if not is_member:
            print("非會員，僅能下載圖片")
            mode = "image"
            # 擷取圖片連結與標題
            image_links, titles = get_image_links(driver, main_page, is_member, mode)
            if image_links:
                # 執行圖片下載
                download_images(driver, image_links, titles, desktop_base, mode)
                print("下載完成！")
            return

        # 會員可選擇資源下載或圖片下載
        print("請選擇操作：")
        print("1. 資源下載")
        print("2. 圖片下載")
        choice = input("輸入選項編號：").strip()

        if choice == "1":
            print("你選擇了資源下載")
            mode = "resource"
        elif choice == "2":
            print("你選擇了圖片下載")
            mode = "image"
        else:
            print("無效的選項，程式結束。")
            return

        # 擷取圖片連結與標題（依模式不同擷取方式不同）
        image_links, titles = get_image_links(driver, main_page, is_member, mode)
        if not image_links:
            return

        # 執行下載（資源下載與圖片下載流程不同）
        download_images(driver, image_links, titles, desktop_base, mode)

        print("下載完成！")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()

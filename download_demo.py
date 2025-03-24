from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import sqlite3
import uuid
import requests
import random
import pandas as pd
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import threading

from html_parser import HTMLParser
# Thread lock cho database
db_lock = threading.Lock()

# Constants
MAX_THREADS = 5
STEP_PER_PAGE = 32
FILE_PREFIX = "https://drive.google.com/file/d"
DOWNLOAD_TIMEOUT = 3

# JavaScript để tải PDF
js_download = """
    let jspdf = document.createElement("script");
    jspdf.onload = function () {
        let pdf = new jsPDF();
        let elements = document.getElementsByTagName("img");
        for (let i in elements) {
            let img = elements[i];
            if (!/^blob:/.test(img.src)) { continue; }
            let canvasElement = document.createElement('canvas');
            let con = canvasElement.getContext("2d");
            canvasElement.width = img.width;
            canvasElement.height = img.height;
            con.drawImage(img, 0, 0, img.width, img.height);
            let imgData = canvasElement.toDataURL("image/jpeg", 1.0);
            pdf.addImage(imgData, 'JPEG', 0, 0);
            pdf.addPage();
        }
        pdf.save(arguments[0]);
    };
    jspdf.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/1.3.2/jspdf.min.js';
    document.body.appendChild(jspdf);
"""

def get_driver():
    """Khởi tạo Selenium WebDriver."""
    options = Options()
    prefs = {
        "download.default_directory": "./Storage",
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    options.add_argument('--disable-dev-shm-usage')
    options.add_experimental_option('prefs', prefs)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def create_database():
    """Tạo database."""
    connection = sqlite3.connect("storage.db")
    cursor = connection.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_identifier TEXT,
                        name TEXT,
                        datakey TEXT,
                        path TEXT
                    )""")
    connection.commit()
    connection.close()

def insert_file_record(file_identifier, name, datakey, path):
    """Thread-safe insert vào database."""
    with db_lock:
        connection = sqlite3.connect("storage.db")
        cursor = connection.cursor()
        insert_query = "INSERT INTO files (file_identifier, name, datakey, path) VALUES (?, ?, ?, ?)"
        cursor.execute(insert_query, (file_identifier, name, datakey, path))
        connection.commit()
        connection.close()

def download_file_in_tab(driver, file_url, filename, datakey, path):
    """Tải file trong một tab."""
    try:
        # Mở tab mới
        driver.execute_script(f"window.open('{file_url}');")
        time.sleep(random.uniform(1, 3))
        driver.switch_to.window(driver.window_handles[-1])  # Chuyển sang tab mới nhất

        # Cuộn trang và tải file
        action = ActionChains(driver)
        pages_element = driver.find_element(By.CSS_SELECTOR, ".ndfHFb-c4YZDc-DARUcf-NnAfwf-j4LONd")
        pages_number = int(pages_element.text)

        for _ in range(STEP_PER_PAGE * pages_number):
            action.key_down(Keys.ARROW_DOWN).key_up(Keys.ARROW_DOWN).perform()
            time.sleep(0.05)

        unique_id = str(uuid.uuid4()).replace("-", "")
        insert_file_record(unique_id, filename, datakey, path)

        filename = f"{unique_id}-{filename}.pdf"
        driver.execute_script(js_download, filename)
        time.sleep(DOWNLOAD_TIMEOUT)

        # Đóng tab sau khi tải xong
        driver.close()
        driver.switch_to.window(driver.window_handles[0])  # Quay lại tab chính
    except Exception as e:
        print(f"Error downloading {file_url}: {e}")

def download_handler(driver, target_url, datakey):
    """Xử lý tải file hoặc thư mục."""
    if target_url.startswith(FILE_PREFIX):
        response = requests.get(target_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        title_element = soup.find("title")
        download_file_in_tab(driver, target_url, title_element.text, datakey, "")
    else:
        # Xử lý thư mục (giữ nguyên logic cũ nhưng dùng tab)
        response = requests.get(target_url)
        html_content = response.text
        parser = HTMLParser(html_content=html_content)
        files_info, folders_info = parser.parse_html()
        for file in files_info:
            download_file_in_tab(driver, file['api'], file['name'], datakey, "")

def main_driver():
    """Main function với một WebDriver duy nhất và nhiều tab."""
    create_database()
    storage_df = pd.read_csv("documents.csv")
    used_df = storage_df[~storage_df['url'].isnull()]

    urls = [(url, datakey) for datakey, url in zip(used_df['datakey'], used_df['url'])]

    # Khởi tạo một WebDriver duy nhất
    driver = get_driver()
    driver.get("https://drive.google.com")  # Mở trang chính

    # Xử lý từng URL trong danh sách
    for url, datakey in urls:
        download_handler(driver, url, datakey)

    # Đóng WebDriver sau khi hoàn thành
    driver.quit()

main_driver()
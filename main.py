from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import time
import sqlite3
import json
import requests

options = Options()

prefs = {
    "download.default_directory": "./Storage",  # Set download folder
    "download.prompt_for_download": False,  # No prompt
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True  # Open PDFs externally instead of Chrome viewer
}

options.add_argument('--disable-dev-shm-usage')
options.add_experimental_option('prefs', prefs)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)



driver.get("https://tailieuchuan.vn/")


api_prefix = "https://tailieuchuan.vn"

connection = sqlite3.connect("link_storage.db")
cursor = connection.cursor()



def scrape_category_paths():
    api_categories = []
    
    try:
        driver.get("https://tailieuchuan.vn/")
        time.sleep(2)

        menu_element = driver.find_element(By.CSS_SELECTOR, "#menu_main")
        menu_item_columns = menu_element.find_elements(By.CSS_SELECTOR, ".categories-box > div:nth-of-type(1) > div")  
        # print(menu_element.get_attribute("outerHTML"))
        for column in menu_item_columns:
            # print("Column: ", column.get_attribute("outerHTML"))
            categories = column.find_elements(By.CSS_SELECTOR, ".parent-category")
            for category in categories:
                # print("Category: ", category.get_attribute("outerHTML"))
                category_url = category.find_element(By.CSS_SELECTOR, "span > a").get_attribute("data-href")
                category_name = category_url.split("/")[-1].split(".")[0]
                # print(f"Category: {category_name} - {category_url}")
                api_categories.append({"name": category_name, "url": api_prefix + category_url})
                # handle_category(category_name, category_url)
        
        return api_categories
    except Exception as e:
        print(f"Error: {e}")
   

categories_dict = scrape_category_paths()

def create_table():
    cursor.execute('''CREATE TABLE IF NOT EXISTS documents
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT,
                    type TEXT, category TEXT, price DOUBLE, datakey TEXT, url TEXT)''')
    connection.commit()

def scrape_category(category_name, category_url):
    try:
        driver.get(category_url)
        time.sleep(2)

        document_types = driver.find_elements(By.CSS_SELECTOR, ".table-responsive > div:nth-of-type(1) > .table > tbody > tr")
        type_urls = []
        for document_type in document_types:
            url = document_type.find_element(By.CSS_SELECTOR, "td > a").get_attribute("href")
            # print(url)
            type_urls.append(url)

        for url in type_urls:
            driver.get(url)
            time.sleep(2)

            document_container = driver.find_element(By.CSS_SELECTOR, ".p-1")
            documents = document_container.find_elements(By.CSS_SELECTOR, ".highlight")
            # print(len(documents))
            name_type = url.split("/")[-1].split(".")[0]
            document_blocks = []
            for document in documents:
                url = document.find_element(By.CSS_SELECTOR, ".box-title > div:nth-of-type(1) > a").get_attribute("href")
                document_block = {
                    "document_type": name_type,
                    "api": url
                }
                document_blocks.append(document_block)
            for document_info in document_blocks:
                print(f"Document get into flag")
                document_api = document_info['api']
                driver.get(document_api)
                time.sleep(2)
                

                document_name_ele = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".document-main-info > div:nth-of-type(1) > a"))
                )
                document_name = document_name_ele.text.strip()

                print(f"Document Name: {document_name}")

                price_eles = driver.find_elements(By.CSS_SELECTOR, ".detail-price > div:nth-of-type(1) > span:nth-of-type(2)")
                if len(price_eles) == 0:
                    price_ele = driver.find_element(By.CSS_SELECTOR, ".my-2 > span:nth-of-type(2)")
                else:  
                    price_ele = price_eles[0]
                price = price_ele.text.split(" ")[0]
                if price == "MIỄN":
                    price = 0
                else:
                    price = str(price).replace(",", "")
                    price = float(price)
                print(f"Price: {price}")
                print(f"type: {document_info['document_type']}")
                print(f"Category: {category_name}")

                data_key = document_api.split("/")[-1].split(".")[0].split("-")[-1]
                
                crawl_url = "https://tailieuchuan.vn/document/preview"
                crawl_headers = {
                    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br, zstd",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-CSRF-TOKEN": "koB3Y54mxY0GGlX8aMNQiU4GCd3Zua84NDrv5x7W",
                    "X-Requested-With": "XMLHttpRequest",
                    "Origin": "https://tailieuchuan.vn",
                    "Referer": "https://tailieuchuan.vn/bo-de-luyen-thi-thu-vip-danh-gia-nang-luc-hsa-form-2025-dai-hoc-quoc-gia-ha-noi-25302.html",
                    "Cookie": "XSRF-TOKEN=eyJpdiI6Ik43bkIzVzgxckd3WUpPRW0zVWZIVmc9PSIsInZhbHVlIjoiUUJYckJ3c01IcWd3L2lJdnB6VG1LV0JDOXVINlYxZzRTUEVXY3AwVjB0QzhtZk9ldm5UUmpTUUFkZ1J5YmlONG0xL0ZINEpPTWU4eFZxTmduYk5TUHRYZ1VhL2dhYnB3NTRtV3ZNb05iSGlCcCt6VFk1OVlxMERSem45cndJaTYiLCJtYWMiOiIwNzVjM2Q0MWZhM2ZjZGU5ZjA2NzJmMDVlYzU3MjBiMDMyMjllOWY4MzI1MTUzMzdjYTkyNzEwNTYzYzFiNmQ3IiwidGFnIjoiIn0%3D; tailieuchuan_prod_session=eyJpdiI6IkVZemZRa2RoVGNPRTR3NExxM1pwOVE9PSIsInZhbHVlIjoiT1Y3NW5tZUNKNmpZT0JxVEN1dzMyYjNVTE43bmgzT3NrMHhKN24yMUUrM0FZNVVnV2wvMXVnZEFrWWNpTFFwc3BzSTFMSENIR3ZmSUdidlNnV2VIalFwRTZZdFl3V2ZFWGJYbVBkL2JXUmdGYjZGeE0zM1FDSzdieHBwa01iaTgiLCJtYWMiOiIxOWZmMGRjMTFiMWExY2U0ZDVlM2IwYmZmODVjNDhjYmI1ZmZmNDE0MTk1NjMyYjFlNmFlMjIzNmNjNzYxYjhhIiwidGFnIjoiIn0%3D",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-origin",
                    "Priority": "u=0",
                    "TE": "trailers"
                }

                crawl_data = {
                    "_token": "koB3Y54mxY0GGlX8aMNQiU4GCd3Zua84NDrv5x7W",
                    "id": data_key,
                    "is_mobile": "false"
                }

                response = requests.post(crawl_url, headers=crawl_headers, data=crawl_data)

                data_url = response.json()['link']
                print(f"Data_url: {data_url}")

                cursor.execute("INSERT INTO documents (name, type, category, price, datakey, url) VALUES (?,?,?,?,?,?)",
                                (document_name, document_info['document_type'], category_name, price, data_key, data_url))
                connection.commit()


    except Exception as e:
        print(f"Error: {e}")


def scrape_all_courses():
    for category in categories_dict:
        scrape_category(category["name"], category["url"])

def main_driver():
    create_table()
    scrape_all_courses()

main_driver()

driver.quit()

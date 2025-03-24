from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import undetected_chromedriver as uc
import time
import sqlite3
import requests
import uuid
import random
import subprocess

import pandas as pd
from bs4 import BeautifulSoup


from html_parser import HTMLParser
from json_template import TEMPLATE_JSON

connection = sqlite3.connect("storage.db")
cursor = connection.cursor()

options = Options()

prefs = {
    "download.default_directory": "./Storage",  # Set download folder
    "download.prompt_for_download": False,  # No prompt
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True  # Open PDFs externally instead of Chrome viewer
}

options.add_argument('--disable-dev-shm-usage')
options.add_experimental_option('prefs', prefs)


# Trusted Type policy 
js_trusted_policy = """
    const policy = window.trustedTypes.createPolicy("default", {
    createScriptURL: (input) => input, // Ensure input is sanitized
  });
  
  // Use it when setting script sources
  const scriptElement = document.createElement("script");
  scriptElement.src = policy.createScriptURL("https://example.com/script.js");
  document.body.appendChild(scriptElement);
"""


# download pdf function
js_download = """
    let jspdf = document.createElement( "script" );
jspdf.onload = function () {
let pdf = new jsPDF();
let elements = document.getElementsByTagName( "img" );
for ( let i in elements) {
let img = elements[i];
if (!/^blob:/.test(img.src)) {
continue ;
}
let canvasElement = document.createElement( 'canvas' );
let con = canvasElement.getContext( "2d" );
canvasElement.width = img.width;
canvasElement.height = img.height;
con.drawImage(img, 0, 0,img.width, img.height);
let imgData = canvasElement.toDataURL( "image/jpeg" , 1.0);
pdf.addImage(imgData, 'JPEG' , 0, 0);
pdf.addPage();
}
pdf.save( "download.pdf" );
};
jspdf.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/1.3.2/jspdf.min.js' ;
document.body.appendChild(jspdf);
"""
# Constant for running
step_per_page = 32
# Prefix for url
file_prefix = "https://drive.google.com/file/d"
# THREAD
THREADS = 5


driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
# driver = uc.Chrome(options=options)
driver.get("https://drive.google.com")

NORDVPN_COUNTRIES = ["us", "uk", "de", "fr", "ca", "au"]

def switch_vpn_server():
    """Thay đổi server VPN NordVPN ngẫu nhiên."""
    country = random.choice(NORDVPN_COUNTRIES)
    try:
        # Ngắt kết nối VPN hiện tại
        subprocess.run(["nordvpn", "disconnect"], check=True)
        time.sleep(1)  # Đợi ngắt kết nối hoàn tất
        
        # Kết nối đến server mới
        print(f"Đang kết nối đến server NordVPN tại {country.upper()}...")
        subprocess.run(["nordvpn", "connect", country], check=True)
        time.sleep(5)  # Đợi kết nối ổn định
        print(f"Đã kết nối đến {country.upper()}!")
    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi thay đổi server VPN: {e}")
        return False
    return True

def createDatabase():
    cursor.execute("""CREATE TABLE IF NOT EXISTS files (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            file_identifier TEXT,
                            name TEXT,
                            datakey TEXT,
                            path TEXT
                        )""")
   
    connection.commit()

def download_file(file_url, filename="download.pdf", datakey="", path="", switch_vpn=False):
    if switch_vpn:
        switch_vpn_server()
    time.sleep(random.uniform(1, 5))
    driver.get(file_url)
    time.sleep(2)
    action = ActionChains(driver)
    pages_element = driver.find_element(By.CSS_SELECTOR, ".ndfHFb-c4YZDc-DARUcf-NnAfwf-j4LONd")
    pages_number = int(pages_element.text)
    print(pages_number)

    for _ in range(step_per_page*pages_number):  # Adjust the range for more scrolling
        action.key_down(Keys.ARROW_DOWN).key_up(Keys.ARROW_DOWN).perform()
        time.sleep(0.05)

    unique_id = uuid.uuid4()
    unique_id = str(unique_id).replace("-", "")
    insert_query = "INSERT INTO files (file_identifier, name, datakey, path) VALUES (?, ?, ?, ?)"
    cursor.execute(insert_query, (unique_id, filename, datakey, path))
    connection.commit()

    time.sleep(0.5)
    driver.execute_script(js_trusted_policy)
    filename = str(unique_id) + "-" + filename + ".pdf"
    custom_js_download = js_download.replace('"download.pdf"', f'"{filename}"')
    driver.execute_script(custom_js_download)
    time.sleep(3)


def remove_last_path(path_str):
    rm_path = path_str.split('/')[-1]
    path_str = path_str.replace(f"/{rm_path}", "")
    return path_str

info_path = ""

def folder_handler(folder_url, datakey, switch_vpn):
    global info_path
    response = requests.get(folder_url)
    html_content = response.text
    parser = HTMLParser(html_content=html_content)
    self_item_name = parser.name
    info_path += f"/{self_item_name}"
    files_info, folders_info = parser.parse_html()

    if(len(folders_info) == 0):
        for file in files_info:
            info_path += f"/{file['name']}"
            download_file(file_url=file['api'], filename=file['name'], datakey=datakey, path=info_path, switch_vpn=switch_vpn)
            info_path = remove_last_path(info_path)
    else:
        for folder in folders_info:
            category_info = f"{folder['name']}"
            if "Google Drive" in category_info:
                if " - Google Drive" in category_info:
                    category_info = category_info.replace("Google Drive - ","")
                if "Google Drive Folder: " in category_info:
                    category_info = category_info.replace("Google Drive Folder: ","")
                if "Google Drive" in category_info:
                    category_info = category_info.replace("Google Drive","")
            info_path += f"/{category_info}"
            folder_handler(f"{folder_url}/{folder['api']}", datakey, switch_vpn=switch_vpn)
            info_path = remove_last_path(info_path)

    

def download_handler(target_url, datakey, switch_vpn):
    if target_url.startswith(file_prefix):
        response = requests.get(target_url)
        html_content = response.text
        soup = BeautifulSoup(html_content)
        title_element = soup.find("title")
        download_file(target_url, filename= title_element.text, datakey=datakey, switch_vpn=switch_vpn)
    else:
        folder_handler(target_url, datakey=datakey, switch_vpn=switch_vpn)

createDatabase()

# download_handler(target_url="https://drive.google.com/drive/u/0/folders/1xVCcvUHQoBX3cEZf3ydKovKgJd4F03IF", datakey="1234")

def main_driver():
    storage_df = pd.read_csv("documents.csv")
    used_df = storage_df[~storage_df['url'].isnull()]

    createDatabase()
    i = 0
    for datakey, url in zip(used_df['datakey'], used_df['url']):
        switch_vpn = (i % 2 == 0)
        download_handler(url, datakey, switch_vpn)
        i = i + 1
        
main_driver()

driver.quit()




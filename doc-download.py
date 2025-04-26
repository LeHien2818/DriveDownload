from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from PIL import Image
from PyPDF2 import PdfMerger

import os
import shutil
import time
import sqlite3
import requests
import random

from bs4 import BeautifulSoup
import argparse

from html_parser import HTMLParser
connection = sqlite3.connect("storage.db")
cursor = connection.cursor()

options = Options()


options.add_argument('--disable-dev-shm-usage')


def parse_args():
    parser = argparse.ArgumentParser(description="Tải file từ Google Drive và xử lý PDF/DOCX")
    parser.add_argument('--url', type=str, required=True,
                        help='URL của file hoặc thư mục Google Drive để tải')
    return parser.parse_args()

# Constant for running
step_per_page_doc = 15
step_per_page_pdf = 32
# Prefix for url
file_prefix = "https://drive.google.com/file/d"
# THREAD
THREADS = 5


driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
# driver = uc.Chrome(options=options)
driver.get("https://drive.google.com")


def createDatabase():
    cursor.execute("""CREATE TABLE IF NOT EXISTS files (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT,
                            path TEXT
                        )""")
   
    connection.commit()


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

set_opacity_js = """
    document.querySelectorAll('.ndfHFb-c4YZDc-q77wGc').forEach(element => {
    element.style.setProperty('opacity', '0', 'important');
});
"""

def download_file(file_url, filename="download.pdf", path=""):
    storage_dir = "doc_data"
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)
    
    time.sleep(random.uniform(1, 5))
    driver.get(file_url)
    time.sleep(2)
    action = ActionChains(driver)
    pages_element = driver.find_element(By.CSS_SELECTOR, ".ndfHFb-c4YZDc-DARUcf-NnAfwf-j4LONd")
    pages_number = int(pages_element.text)
    # print(pages_number)

    for _ in range(step_per_page_pdf*pages_number):  # Adjust the range for more scrolling
        action.key_down(Keys.ARROW_DOWN).key_up(Keys.ARROW_DOWN).perform()
        time.sleep(0.05)

    insert_query = "INSERT INTO files (name, path) VALUES (?, ?)"
    cursor.execute(insert_query, (filename, path))
    connection.commit()

    time.sleep(0.5)
    driver.execute_script(js_trusted_policy)
    filename = f"{filename}.pdf"
    custom_js_download = js_download.replace('"download.pdf"', f'"{filename}"')
    filename = filename.replace(":", "_")
    driver.execute_script(custom_js_download)
    time.sleep(3)
    
    # move file to the expected location
    download_default_path = "/home/lehien/Downloads" # change this to your default download folder
    file_source_path = f"{download_default_path}/{filename}"
    dir_path = remove_last_path(path_str=path)
    destination_path = f"./doc_data{dir_path}"

    if not os.path.exists(destination_path):
        os.makedirs(destination_path)
    
    shutil.move(str(file_source_path), str(destination_path))




def download_file_docx(file_url, filename="download.pdf", path=""):
    output_dir = "screenshots"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    
    # time.sleep(random.uniform(1, 5))
    driver.get(file_url)
    driver.set_window_size(1024, 1024)
    driver.set_window_rect(20, 20, 1024, 1024)
    time.sleep(2)
    action = ActionChains(driver)
    pages_element = driver.find_element(By.CSS_SELECTOR, ".ndfHFb-c4YZDc-DARUcf-NnAfwf-j4LONd")
    pages_number = int(pages_element.text)
    # print(pages_number)
    driver.execute_script(set_opacity_js)
    screenshots = []
    for i in range(0, pages_number * 2): 
        driver.execute_script(set_opacity_js) # Adjust the range for more scrolling
        screenshot_path= f"{output_dir}/page_{i}.png"
        driver.save_screenshot(screenshot_path)
        screenshots.append(screenshot_path)
        for _ in range(0, step_per_page_doc):
            action.key_down(Keys.ARROW_DOWN).key_up(Keys.ARROW_DOWN).perform()
            time.sleep(0.1)
    driver.execute_script(set_opacity_js)

    insert_query = "INSERT INTO files (name, path) VALUES (?, ?)"
    cursor.execute(insert_query, (filename, path))
    connection.commit()

    pdf_merger = PdfMerger()

    for screenshot in screenshots:
        # Convert PNG to PDF-compatible format
        image = Image.open(screenshot)
        pdf_path = screenshot.replace(".png", ".pdf")
        image.save(pdf_path, "PDF", resolution=100.0)
        pdf_merger.append(pdf_path)

    # Save the combined PDF
    # storage_dir = "doc_data"
    dir_path = remove_last_path(path_str=path)
    storage_dir = f"./doc_data{dir_path}"

    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)


    output_pdf = os.path.join(storage_dir, f"{filename}.pdf")
    pdf_merger.write(output_pdf)
    pdf_merger.close()

    # Clean up temporary files (optional)
    for file in screenshots:
        os.remove(file)
    for file in [f.replace(".png", ".pdf") for f in screenshots]:
        os.remove(file)
        


def remove_last_path(path_str):
    rm_path = path_str.split('/')[-1]
    path_str = path_str.replace(f"/{rm_path}", "")
    return path_str

info_path = ""

# DFS traversal
def folder_handler(folder_url):
    global info_path
    # print(info_path)
    response = requests.get(folder_url)
    html_content = response.text
    parser = HTMLParser(html_content=html_content)
    self_item_name = parser.name
    # info_path += f"/{self_item_name}"
    files_info, folders_info = parser.parse_html()
    if(len(files_info) != 0):
        for file in files_info:
            if(file['type'] == "pdf"):
                info_path += f"/{file['name']}"
                download_file(file_url=file['api'], filename=file['name'], path=info_path)
            else:
                info_path += f"/{file['name']}"
                download_file_docx(file_url=file['api'], filename=file['name'], path=info_path)
            print('-----------------before-----------------')
            print(info_path)
            info_path = remove_last_path(info_path)
            print('----------------after remove------------')
            print(info_path)

    if(len(folders_info) == 0):
        print("End nested traversing!")
    else:
        print("-----------------------------------------------")
        print(len(folders_info))
        print("---------------length--------------------------")
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
            folder_handler(f"{folder_url}/{folder['api']}")
            
            info_path = remove_last_path(info_path)
            

    

def download_handler(target_url):
    createDatabase()
    storage_dir = "doc_data"
    if os.path.exists(storage_dir):
        try:
            shutil.rmtree(storage_dir)  # Xóa cưỡng chế thư mục và nội dung
            print(f"Đã xóa thư mục {storage_dir}")
        except PermissionError:
            print(f"Lỗi: Không có quyền xóa thư mục {storage_dir}")
        except OSError as e:
            print(f"Lỗi khi xóa thư mục {storage_dir}: {e}")
    
    if target_url.startswith(file_prefix):
        response = requests.get(target_url)
        html_content = response.text
        soup = BeautifulSoup(html_content)
        title_element = soup.find("title")
        if "pdf" in str(title_element.text):
            download_file(target_url, filename= title_element.text)
        else:
            download_file_docx(target_url, filename=title_element.text)
    else:
        folder_handler(target_url)

createDatabase()

def main_driver():
    # Nhận URL từ terminal
    args = parse_args()
    target_url = args.url
    download_handler(target_url=target_url)

if __name__ == '__main__':
    main_driver()
    driver.quit()





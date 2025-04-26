# Prerequiste

- OS: Linux
- Python 3.10
- Chrome

# Installation
 - Checkout the requirement.txt file to install neccessary package to run the tool
 - Create a file "storage.db" in root folder in case there is no such a file in the project

 # Usage
 - Inside doc-download.py:
 change line 136 :
 ```
 download_default_path = "/home/lehien/Downloads" # change this to your default download folder
 ```
 - Inside project, run:
 ```
 python doc-download.py --url <the drive links that you want to download>
 ```
 Example:
 ```
 python doc-download.py --url https://drive.google.com/drive/folders/11M6oe9mb_tCeuC7kYRg2AVhK-rBl8_wy
 ```

 In some case if the tool doesn't work properly, before running, opening chrome, and install Disable Content-Security-Policy extension.

# Cautions for developer whom continue developing this tool:
- screenshots is an empty folder used for saving temporary images when gathering from links. Don't remove or change the name
- link_storage.db is all the document links in the tailieuchuan.vn. Some of them is empty because the website hasn't uploaded yet.
- jspdf.min.js is the alternative solution if the link https://cdnjs.cloudflare.com/ajax/libs/jspdf/1.3.2/jspdf.min.js dead.
- install sqlite viewer extension on vscode to observe data in "*.db" files.
## Features
- Can download folders and files which is download restricted and only viewable from Google drive.
- Currently supporting file format: pdf, docx, doc, ppt.
## Limitation
- No supporting video files yet.
- Single thread.
- No batch downloading yet.
- Using sqlite for fast setup but hard to upscale.
- Need GUI.
- All the logic inside one file :)))))), Refactor it!

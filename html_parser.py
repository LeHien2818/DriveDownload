from bs4 import BeautifulSoup

file_identifier_class = "WYuW0e Ss7qXc"
folder_identifier_class = "WYuW0e RDfNAe Ss7qXc"


class HTMLParser:
    
    def __init__(self, html_content):
        self.html_content = html_content
        self.soup = BeautifulSoup(self.html_content, 'html.parser')
        self.name = self.soup.find('title').text
    
    def get_all_file_elements(self):
        files = []
        elements = self.soup.find_all(class_=file_identifier_class)
        
        for element in elements:
            # print(element.get('data-id'))
            type_container = element.find(class_="tyTrke M3pype")
            file_name_container = type_container.find(class_="KL4NAf")
            file_name = file_name_container.get('data-tooltip')
            file_type = file_name.split('.')[-1]
            file_name = file_name.replace(f".{file_type}", "")
            # Skip file with extension which is not pdf
            if (file_type == "pdf"):
                # print(file_name)
                data = {
                    'id': element.get('data-id'),
                    'name': file_name,
                    'type': file_type,
                }
                files.append(data)
            else:
                # print(file_name)
                data = {
                    'id': element.get('data-id'),
                    'name': file_name ,
                    'type': file_type,
                }
                files.append(data)
        # print(len(files))
        return files

    def get_all_subfolder_elements(self):
        subfolders = []
        elements = self.soup.find_all(class_=folder_identifier_class)
        # print(len(elements))
        for element in elements:
            # print(element.get('data-id'))
            type_container = element.find(class_="tyTrke M3pype")
            folder_name_container = type_container.find(class_="KL4NAf")
            folder_name = folder_name_container.get('data-tooltip')
            data = {
                'id': element.get('data-id'),
                'name': folder_name,
            }
            subfolders.append(data)
        return subfolders
    
    def isFolderLeft(self):
        flag = True
        folder_ids = self.get_all_subfolder_elements()
        if len(folder_ids) == 0:
            flag = False
        return flag

    def parse_html(self):
        # Implement HTML parsing logic here
        # Use BeautifulSoup or similar libraries to extract the required data
        prefix_file_api = "https://drive.google.com/file/d/"
        prefix_folder_api = "https://drive.google.com/drive/folders/"
        files = self.get_all_file_elements()
        folders = self.get_all_subfolder_elements()
        files_info = []
        folders_info = []
        for file in files:
            file_api = f"{prefix_file_api}{file['id']}/view"
            file_name = file['name']
            files_info.append({
                'name': file_name,
                'api': file_api,
                'type': file['type']
            })
        for folder in folders:
            folder_api = f"{prefix_folder_api}{folder['id']}"
            folder_name = folder['name']
            folders_info.append({
                'name': folder_name,
                'api': folder_api,
            })

        print(f"Files: {files_info}")
        print(f"Folders: {folders_info}")
        return files_info, folders_info


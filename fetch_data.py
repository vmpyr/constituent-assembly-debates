import requests
from bs4 import BeautifulSoup
import os

def fetch_volume_page(url_volume):
    response = requests.get(url_volume)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        link_list = soup.find_all('a', class_='absolute inset-0')
        hrefs = [link.get('href') for link in link_list if link.get('href')]
        return hrefs
    else:
        print(f"Failed to retrieve page. Status code: {response.status_code}")
        return None

def fetch_date_page(url_page):
    response = requests.get(url_page)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    else:
        print(f"Failed to retrieve page. Status code: {response.status_code}")
        return None

def save_html_data(vol, deb_date, page_data):
    if vol < 10: vol = f"0{vol}"
    volume_folder = f"volume_{vol}"
    os.makedirs(volume_folder, exist_ok=True)
    file_path = os.path.join(volume_folder, f"{deb_date}.html")

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(str(page_data))

if __name__ == "__main__":
    for vol in range(1, 13):
        url_volume = f"https://www.constitutionofindia.net/constituent-assembly-debate/volume-{vol}/"
        links = fetch_volume_page(url_volume)

        if links:
            for url_page in links:
                print(url_page)
                page_data = fetch_date_page(url_page)
                if page_data:
                    deb_date = url_page.split('/')[-2]
                    save_html_data(vol, deb_date, page_data)
                else:
                    print(f"Failed to fetch data for {url_page}.")
        else:
            print(f"No links found for volume {vol}.")

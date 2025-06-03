# File: scripts/download_legiscan_zips.py
import os
import requests
from bs4 import BeautifulSoup

os.makedirs("data/zips", exist_ok=True)

BASE_URL = "https://legiscan.com/datasets"
STATE = "IL"

def get_dataset_links():
    print("🔍 Scraping dataset links for Illinois...")
    r = requests.get(BASE_URL)
    soup = BeautifulSoup(r.text, 'html.parser')
    links = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and href.endswith(".zip") and f"/{STATE}_" in href:
            links.append("https://legiscan.com" + href)
    return links

def download_zips(links):
    for url in links:
        filename = os.path.basename(url)
        filepath = os.path.join("data/zips", filename)
        if not os.path.exists(filepath):
            print(f"⬇️ Downloading {filename}...")
            with requests.get(url, stream=True) as r:
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
        else:
            print(f"✅ Skipping {filename} (already downloaded)")

if __name__ == "__main__":
    links = get_dataset_links()
    download_zips(links)

import os
import requests
from bs4 import BeautifulSoup

# Base URL for datasets
BASE_URL = "https://legiscan.com/datasets"
OUTPUT_DIR = "datasets"
TARGET_STATES = ["US", "IL"]

os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_download_links():
    page = requests.get(BASE_URL)
    soup = BeautifulSoup(page.content, "html.parser")
    rows = soup.find_all("tr")
    download_links = []

    for row in rows:
        cells = row.find_all("td")
        if not cells or len(cells) < 2:
            continue
        state = cells[0].text.strip()
        if state in TARGET_STATES:
            links = row.find_all("a", href=True)
            for link in links:
                if "json" in link["href"]:
                    download_links.append(("{}_{}".format(state, link["href"].split("/")[-1]), link["href"]))

    return download_links

def download_files():
    for filename, url in get_download_links():
        print(f"Downloading {filename} from {url}")
        r = requests.get(url)
        if r.status_code == 200:
            with open(os.path.join(OUTPUT_DIR, filename), "wb") as f:
                f.write(r.content)
        else:
            print(f"Failed to download {url}")

if __name__ == "__main__":
    download_files()

# scripts/fetch_loc_combined.py
import os
import hashlib
import time
import requests
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://www.loc.gov/collections/?q="
KEYWORDS = [
    "negro","slavery","enslaved people","slave","plantation",
    "freedmen","black panther","civil rights","escaped slave",
    "underground railroad","fred hampton","colored people","jim crow","segregation"
]

session = requests.Session()
retries = Retry(
    total=5, backoff_factor=1,
    status_forcelist=[500,502,503,504],
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)

def fetch_results(keyword, max_pages=2):
    items = []
    for page in range(1, max_pages + 1):
        url = f"{BASE_URL}{requests.utils.quote(keyword)}&sp={page}&fo=json"
        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json().get("results", [])
            if not data:
                break
            items.extend(data)
            time.sleep(1)
        except Exception as e:
            print(f"Error fetching {keyword} page {page}: {e}")
            break
    return items

def sanitize_title(title):
    safe = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).strip()
    return safe.replace(" ", "-")[:50]

def save_text_and_images(keyword, items):
    POSTS_DIR = "_posts"
    IMAGES_DIR = "images"
    os.makedirs(POSTS_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    date_str = datetime.utcnow().strftime("%Y-%m-%d")

    for item in items:
        title = item.get("title", "Untitled")
        url = item.get("url", "")
        desc = item.get("description", ["No description"])[0]
        uid = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"{POSTS_DIR}/{date_str}-{sanitize_title(title)}-{uid}.md"

        # Write markdown file if doesn't exist
        if not os.path.exists(filename):
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"---\n")
                f.write(f"title: \"{title}\"\n")
                f.write(f"date: {date_str}\n")
                f.write(f"source: \"{url}\"\n")
                f.write(f"keyword: \"{keyword}\"\n")
                f.write(f"---\n\n")
                f.write(desc + "\n\n")

                # Save image links (if any)
                images = item.get("image", [])
                if images:
                    for idx, img in enumerate(images):
                        img_url = img.get("src") or img.get("url")
                        if not img_url:
                            continue
                        try:
                            img_resp = session.get(img_url, timeout=15)
                            img_resp.raise_for_status()
                            ext = img_url.split(".")[-1].split("?")[0]  # crude extension
                            img_filename = f"{IMAGES_DIR}/{date_str}-{uid}-{idx}.{ext}"
                            with open(img_filename, "wb") as img_file:
                                img_file.write(img_resp.content)
                            f.write(f"![image-{idx}]({img_filename})\n")
                        except Exception as e:
                            print(f"Failed to download image {img_url}: {e}")

if __name__ == "__main__":
    for kw in KEYWORDS:
        print(f"Fetching keyword: {kw}")
        results = fetch_results(kw, max_pages=2)
        save_text_and_images(kw, results)
    print("Done fetching text and images.")

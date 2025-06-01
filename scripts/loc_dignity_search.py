# scripts/fetch_loc.py
import os
import hashlib
import time
import requests
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Same base URL and keywords
BASE_URL = "https://www.loc.gov/collections/?q="
KEYWORDS = [
    "slavery","enslaved people","slave","plantation","African Americans",
    "freedmen","reconstruction","emancipation","civil rights","abolition",
    "underground railroad","black history","negro","colored people","jim crow","segregation"
]

# Set up session with retry logic
session = requests.Session()
retries = Retry(
    total=5, backoff_factor=1,
    status_forcelist=[500,502,503,504],
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)

def fetch_results(keyword, max_pages=1):
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

def save_items(keyword, items):
    POSTS_DIR = "_posts"
    os.makedirs(POSTS_DIR, exist_ok=True)
    date_str = datetime.utcnow().strftime("%Y-%m-%d")

    for idx, item in enumerate(items):
        title = item.get("title", "Untitled")
        url = item.get("url", "")
        desc = item.get("description", ["No description"])[0]
        uid = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"{POSTS_DIR}/{date_str}-{sanitize_title(title)}-{uid}.md"
        if not os.path.exists(filename):
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"---\n")
                f.write(f"title: \"{title}\"\n")
                f.write(f"date: {date_str}\n")
                f.write(f"source: \"{url}\"\n")
                f.write(f"keyword: \"{keyword}\"\n")
                f.write(f"---\n\n")
                f.write(desc)

if __name__ == "__main__":
    # For each keyword, fetch first page and save (change max_pages as needed)
    for kw in KEYWORDS:
        print(f"Fetching keyword: {kw}")
        results = fetch_results(kw, max_pages=2)
        save_items(kw, results)
    print("Done fetching and saving LOC data.")

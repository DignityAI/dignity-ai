import os
import requests
import time
import hashlib
from datetime import datetime

BASE_URL = "https://www.loc.gov/photos/?fo=json&q="
KEYWORDS = [
    "slavery", "enslaved people", "slave", "plantation",
    "African Americans", "freedmen", "reconstruction", "emancipation",
    "civil rights", "abolition", "underground railroad", "black history",
    "negro", "colored people", "jim crow", "segregation"
]
POSTS_DIR = "_posts"
MAX_ITEMS = 10  # Limit each run to 10 new items
DELAY = 2  # Delay between requests (seconds)

def sanitize_filename(title):
    title = title.replace(' ', '-').replace('/', '-')
    return ''.join(c for c in title if c.isalnum() or c in ['-', '_'])[:50]

def save_post(item):
    title = item.get("title", "Untitled")
    url = item.get("url")
    date_str = datetime.now().strftime("%Y-%m-%d")
    hash_id = hashlib.md5(url.encode()).hexdigest()[:8]
    filename = f"{POSTS_DIR}/{date_str}-[{sanitize_filename(title)}-{hash_id}.md"

    if not os.path.exists(POSTS_DIR):
        os.makedirs(POSTS_DIR)

    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write(f"---\ntitle: \"{title}\"\ndate: {date_str}\nsource: {url}\n---\n")
        print(f"Saved: {filename}")

def fetch_batch():
    count = 0
    for keyword in KEYWORDS:
        if count >= MAX_ITEMS:
            break
        try:
            print(f"Searching for: {keyword}")
            response = requests.get(f"{BASE_URL}{requests.utils.quote(keyword)}", timeout=10)
            response.raise_for_status()
            data = response.json()
            items = data.get("results", [])
            for item in items:
                if count >= MAX_ITEMS:
                    return
                save_post(item)
                count += 1
                time.sleep(DELAY)
        except Exception as e:
            print(f"Error for '{keyword}': {e}")
            time.sleep(DELAY)

if __name__ == "__main__":
    fetch_batch()
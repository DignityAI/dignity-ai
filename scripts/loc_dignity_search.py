# fetch_loc_all.py

import requests
import json
from datetime import datetime
from pathlib import Path
import hashlib
import time

KEYWORDS = [
    "slavery", "enslaved people", "slave", "plantation", "African Americans",
    "freedmen", "reconstruction", "emancipation", "civil rights", "abolition",
    "underground railroad", "black history", "negro", "colored people",
    "jim crow", "segregation"
]

BASE_URL = "https://www.loc.gov/search/?fo=json&q="
posts_dir = Path("_posts")
posts_dir.mkdir(parents=True, exist_ok=True)

def sanitize_title(title):
    return title.strip().replace(":", "-").replace("/", "-").replace(" ", "-")[:50]

def save_entry(entry, keyword):
    title = entry.get("title", "No Title")
    safe_title = sanitize_title(title)
    description = entry.get("description", ["No description available."])[0]
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    url = entry.get("url", "")
    uid = hashlib.md5((title + url).encode()).hexdigest()[:8]
    filename = f"{date_str}-{safe_title}-{uid}.md"
    filepath = posts_dir / filename

    if not filepath.exists():
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"---\n")
            f.write(f"title: \"{title}\"\n")
            f.write(f"date: {date_str}\n")
            f.write(f"source: Library of Congress\n")
            f.write(f"loc_url: {url}\n")
            f.write(f"keyword: {keyword}\n")
            f.write(f"---\n\n")
            f.write(description)

def fetch_all_for_keyword(keyword):
    page = 1
    while True:
        print(f"Fetching page {page} for keyword: {keyword}")
        response = requests.get(f"{BASE_URL}{requests.utils.quote(keyword)}&sp={page}")
        if response.status_code != 200:
            print(f"Failed on page {page}: {response.status_code}")
            break

        data = response.json()
        results = data.get("results", [])
        if not results:
            break

        for entry in results:
            save_entry(entry, keyword)

        if "next" not in data.get("pagination", {}):
            break

        page += 1
        time.sleep(1)  # prevent hitting API rate limits

# Main execution
for keyword in KEYWORDS:
    fetch_all_for_keyword(keyword)

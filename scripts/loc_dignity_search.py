import os
import json
import time
import requests
from urllib.parse import quote_plus
from datetime import datetime
from pathlib import Path

# === Keywords for Black History-related LOC search ===
SEARCH_TERMS = [
    "slavery", "enslaved people", "slave", "plantation",
    "African Americans", "freedmen", "reconstruction", "emancipation",
    "civil rights", "abolition", "underground railroad", "black history",
    "negro", "colored people", "jim crow", "segregation"
]

# === Output folder for content ===
OUTPUT_DIR = Path("data/loc")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# === Constants for Library of Congress API ===
BASE_URL = "https://www.loc.gov/search/"
ITEMS_PER_PAGE = 100  # Max allowed

# === Robust fetch function with retries and streaming ===
def fetch_with_retries(url, max_retries=3, backoff_factor=1):
    session = requests.Session()
    retries = requests.adapters.Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[500, 502, 503, 504],
        raise_on_status=False,
    )
    adapter = requests.adapters.HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    try:
        response = session.get(url, timeout=20, stream=True)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] Fetch failed: {e}")
        return None

# === Format LOC result to Markdown ===
def format_markdown(item):
    title = item.get("title", "Untitled")
    date = item.get("date", "")
    url = item.get("url", "")
    description = item.get("description", "")
    return f"""---
title: "{title}"
date: {date}
source: "{url}"
---

**Description:** {description}
"""

# === Save result to file ===
def save_item(item, term, index):
    safe_title = item.get("title", f"{term}-{index}")[:50].replace(" ", "_").replace("/", "-")
    filename = OUTPUT_DIR / f"{term.replace(' ', '_')}_{index}.md"
    content = format_markdown(item)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[SAVED] {filename}")

# === Main loop for all keywords ===
for term in SEARCH_TERMS:
    print(f"\n[SEARCHING] '{term}'")
    page = 1
    total_found = 0

    while True:
        url = f"{BASE_URL}?q={quote_plus(term)}&fo=json&sp={page}&c={ITEMS_PER_PAGE}"
        data = fetch_with_retries(url)

        if not data or "results" not in data:
            print(f"[SKIPPED] No data for page {page} of '{term}'")
            break

        results = data["results"]
        if not results:
            print(f"[DONE] No more results for '{term}' after page {page}")
            break

        for idx, item in enumerate(results):
            save_item(item, term, (page - 1) * ITEMS_PER_PAGE + idx)

        total_found += len(results)
        page += 1

        # LOC rate limiting
        time.sleep(1)

    print(f"[COMPLETE] {total_found} items collected for '{term}'")

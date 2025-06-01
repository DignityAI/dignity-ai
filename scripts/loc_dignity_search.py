import requests
import time
import json
import os

BASE_URL = "https://www.loc.gov/search/?q="
BATCH_SIZE = 50  # <-- pull 10 pages per keyword per run
PROGRESS_FILE = "loc_progress.json"
OUTPUT_DIR = "_posts"

KEYWORDS = [
    "slavery",
    "enslaved people",
    "slave",
    "plantation",
    "African Americans",
    "freedmen",
    "reconstruction",
    "emancipation",
    "civil rights",
    "abolition",
    "underground railroad",
    "black history",
    "negro",
    "colored people",
    "jim crow",
    "segregation",
]

def safe_get(url, retries=3, backoff=5):
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            return resp
        except (requests.exceptions.RequestException) as e:
            print(f"Request failed ({e}), retry {attempt+1}/{retries} in {backoff}s")
            time.sleep(backoff)
    raise Exception(f"Failed to fetch URL after {retries} retries: {url}")

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)

def save_post(content, keyword, page, index):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f"{OUTPUT_DIR}/2025-06-01-[{keyword.replace(' ', '-')}-page{page}-item{index}].md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

def parse_and_save_items(html_content, keyword, page):
    # TODO: Adjust parsing depending on LOC HTML structure.
    # For demo, save entire page content as one post.
    save_post(html_content, keyword, page, 1)

def fetch_batch_for_keyword(keyword, start_page):
    for page in range(start_page, start_page + BATCH_SIZE):
        url = f"{BASE_URL}{requests.utils.quote(keyword)}&sp={page}"
        print(f"Fetching {url}")
        response = safe_get(url)
        if "No results found" in response.text:
            print(f"No more results for '{keyword}' at page {page}. Stopping.")
            return page - 1  # last page with results
        parse_and_save_items(response.text, keyword, page)
        time.sleep(2)  # polite delay between requests
    return start_page + BATCH_SIZE - 1

def main():
    progress = load_progress()
    for keyword in KEYWORDS:
        last_page = progress.get(keyword, 0)
        print(f"Processing '{keyword}', starting from page {last_page + 1}")
        new_last_page = fetch_batch_for_keyword(keyword, last_page + 1)
        progress[keyword] = new_last_page
        save_progress(progress)

if __name__ == "__main__":
    main()

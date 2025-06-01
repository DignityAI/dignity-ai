import os
import requests
import json
import re
from urllib.parse import urlparse
from slugify import slugify  # pip install python-slugify

# === CONFIGURATION ===
SEARCH_QUERY = "African American slavery"
DOWNLOAD_DIR = "loc_images"
NUM_RECORDS = 20  # Limit number of records for test runs
BASE_URL = "https://www.loc.gov/photos/"

# === Ensure directory exists ===
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# === Helper: Clean and create safe filenames ===
def safe_filename(s, max_len=100):
    base = slugify(s)[:max_len]
    return re.sub(r'[^a-zA-Z0-9-_\.]', '_', base)

# === Fetch records from LoC ===
params = {
    "q": SEARCH_QUERY,
    "fo": "json",
    "c": NUM_RECORDS,
    "at": "results"
}
response = requests.get(BASE_URL, params=params)
response.raise_for_status()
data = response.json()

# === Loop through results ===
for idx, item in enumerate(data.get("results", []), start=1):
    title = item.get("title", "Untitled")
    image_url = item.get("image_url", [])
    url = item.get("url", "")
    item_id = item.get("id", f"record-{idx}")

    # Use the first image if available
    if not image_url:
        print(f"[SKIP] No image URL for: {title}")
        continue

    img_url = image_url[0]
    img_ext = os.path.splitext(urlparse(img_url).path)[1] or ".jpg"

    filename_base = safe_filename(title or item_id)
    image_path = os.path.join(DOWNLOAD_DIR, f"{filename_base}{img_ext}")
    meta_path = os.path.join(DOWNLOAD_DIR, f"{filename_base}.json")

    # === Download image ===
    try:
        img_resp = requests.get(img_url, timeout=10)
        img_resp.raise_for_status()
        with open(image_path, "wb") as f:
            f.write(img_resp.content)
        print(f"[OK] Saved image: {image_path}")
    except Exception as e:
        print(f"[ERROR] Failed image download for '{title}': {e}")
        continue

    # === Save metadata ===
    metadata = {
        "title": title,
        "original_url": url,
        "image_url": img_url,
        "loc_id": item_id,
        "description": item.get("description"),
        "date": item.get("date"),
        "subjects": item.get("subject"),
        "source": "Library of Congress"
    }

    try:
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        print(f"[OK] Saved metadata: {meta_path}")
    except Exception as e:
        print(f"[ERROR] Failed to save metadata for '{title}': {e}")

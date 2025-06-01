import os
import json
import requests
from tqdm import tqdm
from time import sleep
from loguru import logger

# === Setup ===
DATA_DIR = "data/loc"
os.makedirs(DATA_DIR, exist_ok=True)

logger.add("loc_log.log", rotation="1 MB")

# === Functions ===

def fetch_data(query, count=10):
    url = f"https://www.loc.gov/search/?q={query}&fo=json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])[:count]
    except requests.RequestException as e:
        logger.error(f"Error fetching data: {e}")
        return []

def download_image(url, path):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Ensure the content is actually an image
        content_type = response.headers.get("Content-Type", "")
        if "image" not in content_type:
            logger.warning(f"URL did not return image content: {url} (content-type: {content_type})")
            return None

        if isinstance(response.content, bytes):
            with open(path, 'wb') as f:
                f.write(response.content)
            logger.info(f"🖼️ Saved image: {path}")
            return path
        else:
            logger.warning(f"Image download failed (not bytes): {url}")
            return None
    except requests.RequestException as e:
        logger.warning(f"Image download error: {e} ({url})")
        return None
    except Exception as e:
        logger.warning(f"Unexpected image error: {e} ({url})")
        return None

def save_entry(entry, index):
    file_path = os.path.join(DATA_DIR, f"entry_{index}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)
    logger.info(f"📄 Saved entry {index} to {file_path}")

# === Main ===

def main():
    query = "African American history"
    results = fetch_data(query, count=20)

    for idx, result in enumerate(tqdm(results, desc="Processing LOC Results")):
        title = result.get("title", "Untitled")
        image_url = result.get("image_url", [None])[0]
        entry = {
            "title": title,
            "date": result.get("date"),
            "description": result.get("description"),
            "url": result.get("url"),
            "image_path": None
        }

        if image_url:
            image_name = f"image_{idx}.jpg"
            image_path = os.path.join(DATA_DIR, image_name)
            downloaded = download_image(image_url, image_path)
            if downloaded:
                entry["image_path"] = image_path

        save_entry(entry, idx)
        sleep(1)  # Be polite to the LOC servers

if __name__ == "__main__":
    main()

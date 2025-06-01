import os
import requests
import hashlib
from urllib.parse import quote
from pathlib import Path
from datetime import datetime
import yaml

# Use same keywords as original
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
    "segregation"
]

# Output directories
POSTS_DIR = Path("_posts/images")
IMAGES_DIR = Path("assets/images/loc-images")
POSTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# LOC search URL
BASE_URL = "https://www.loc.gov/search/"

HEADERS = {
    "User-Agent": "LOC-Image-Fetcher (+https://yourdomain.com)"
}

def fetch_results(keyword, page=1):
    url = f"{BASE_URL}?q={quote(keyword)}&fo=json&sp={page}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] Fetch failed for {keyword} page {page}: {e}")
        return None

def download_image(image_url, identifier):
    try:
        ext = image_url.split(".")[-1].split("?")[0].split("&")[0]
        filename = f"{identifier}.{ext}"
        filepath = IMAGES_DIR / filename

        response = requests.get(image_url, timeout=20)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            f.write(response.content)
        return str(filepath)
    except Exception as e:
        print(f"[WARNING] Failed to download image: {e}")
        return None

def sanitize_filename(title):
    return "".join(c if c.isalnum() or c in "-_" else "-" for c in title.lower()).strip("-")

def write_post(title, description, image_path, loc_url):
    date = datetime.now().strftime("%Y-%m-%d")
    identifier = sanitize_filename(title)[:50]
    hash_id = hashlib.md5(title.encode()).hexdigest()[:8]
    filename = f"{date}-{identifier}-{hash_id}.md"
    post_path = POSTS_DIR / filename

    frontmatter = {
        "title": title,
        "description": description,
        "image": "/" + image_path.replace("\\", "/"),
        "source": loc_url,
        "tags": ["library of congress", "black history", "image", "liberation"],
    }

    content = f"---\n{yaml.dump(frontmatter)}---\n\n{description or ''}"
    with open(post_path, "w", encoding="utf-8") as f:
        f.write(content)

def fetch_images_for_keyword(keyword):
    print(f"[INFO] Fetching: {keyword}")
    for page in range(1, 3):  # limit to 2 pages per keyword
        data = fetch_results(keyword, page)
        if not data or "results" not in data:
            break

        for item in data["results"]:
            if not item.get("image"):
                continue

            image_url = item["image"][0]
            title = item.get("title", "Untitled")
            description = item.get("description", [""])[0]
            loc_url = item.get("url", "")

            identifier = hashlib.md5(title.encode()).hexdigest()[:10]
            image_path = download_image(image_url, identifier)
            if image_path:
                write_post(title, description, image_path, loc_url)

if __name__ == "__main__":
    for keyword in KEYWORDS:
        fetch_images_for_keyword(keyword)

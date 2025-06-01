import os
import re
import requests
from urllib.parse import urljoin

POSTS_DIR = "_posts"
IMAGES_DIR = "images"
os.makedirs(IMAGES_DIR, exist_ok=True)

def extract_url_from_post(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    # Simple regex to extract source URL from frontmatter: source: "URL"
    match = re.search(r'source:\s*"(.*?)"', content)
    if match:
        return match.group(1)
    return None

def fetch_manifest_json(item_url):
    # Usually manifest URL is item_url + '/manifest.json'
    if not item_url.endswith("/"):
        item_url += "/"
    manifest_url = urljoin(item_url, "manifest.json")
    try:
        resp = requests.get(manifest_url, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error fetching manifest for {item_url}: {e}")
        return None

def download_image(img_url, save_path):
    try:
        resp = requests.get(img_url, stream=True, timeout=20)
        resp.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(1024):
                f.write(chunk)
        print(f"Saved image: {save_path}")
    except Exception as e:
        print(f"Failed to download {img_url}: {e}")

def main():
    for filename in os.listdir(POSTS_DIR):
        if not filename.endswith(".md"):
            continue
        post_path = os.path.join(POSTS_DIR, filename)
        item_url = extract_url_from_post(post_path)
        if not item_url:
            print(f"No source URL found in {filename}, skipping.")
            continue

        manifest = fetch_manifest_json(item_url)
        if not manifest:
            continue

        # LOC manifest images are usually in manifest["items"]
        images = manifest.get("items", [])
        if not images:
            print(f"No images found in manifest for {item_url}")
            continue

        # Download images in the manifest
        for idx, img_item in enumerate(images):
            # Image URL usually in img_item["id"]
            img_url = img_item.get("id")
            if not img_url:
                continue

            # Construct local filename: post filename + image index + extension
            ext = os.path.splitext(img_url)[1].split("?")[0] or ".jpg"
            safe_filename = filename.replace(".md", "")
            save_filename = f"{safe_filename}_img{idx+1}{ext}"
            save_path = os.path.join(IMAGES_DIR, save_filename)

            # Skip if already downloaded
            if os.path.exists(save_path):
                print(f"Image already downloaded: {save_filename}")
                continue

            download_image(img_url, save_path)

if __name__ == "__main__":
    main()
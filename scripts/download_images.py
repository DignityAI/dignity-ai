import os
import re
import requests
import hashlib
from urllib.parse import urljoin

POSTS_DIR = "_posts"
IMAGES_DIR = "images"
os.makedirs(IMAGES_DIR, exist_ok=True)

def extract_source_links():
    links = []
    for fname in os.listdir(POSTS_DIR):
        if fname.endswith(".md"):
            with open(os.path.join(POSTS_DIR, fname), encoding="utf-8") as f:
                content = f.read()
                match = re.search(r'source:\s*"(.*?)"', content)
                if match:
                    links.append(match.group(1))
    return links

def get_manifest_url(item_url):
    if not item_url.endswith('/'):
        item_url += '/'
    return urljoin(item_url, 'manifest.json')

def download_images_from_manifest(manifest_url):
    try:
        resp = requests.get(manifest_url, timeout=15)
        data = resp.json()
        canvases = data.get("sequences", [])[0].get("canvases", [])
        for canvas in canvases:
            img_info = canvas.get("images", [])[0].get("resource", {})
            img_url = img_info.get("@id")
            if img_url:
                img_hash = hashlib.md5(img_url.encode()).hexdigest()[:10]
                ext = os.path.splitext(img_url)[-1] or ".jpg"
                img_path = os.path.join(IMAGES_DIR, f"{img_hash}{ext}")
                if not os.path.exists(img_path):
                    img_data = requests.get(img_url).content
                    with open(img_path, "wb") as out_file:
                        out_file.write(img_data)
                    print(f"Saved image: {img_path}")
    except Exception as e:
        print(f"Failed to fetch manifest: {manifest_url} — {e}")

if __name__ == "__main__":
    item_links = extract_source_links()
    for link in item_links:
        if "loc.gov/item" in link:
            manifest_url = get_manifest_url(link)
            print(f"Trying manifest: {manifest_url}")
            download_images_from_manifest(manifest_url)

    print("Done downloading images.")
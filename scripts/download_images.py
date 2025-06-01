import os
import re
import requests
import hashlib
from urllib.parse import urljoin
import time

POSTS_DIR = "_posts"
IMAGES_DIR = "images"
os.makedirs(IMAGES_DIR, exist_ok=True)

def extract_source_links():
    """Extract source URLs from markdown files in _posts directory."""
    links = []
    if not os.path.exists(POSTS_DIR):
        print(f"Warning: {POSTS_DIR} directory not found!")
        return links
    
    for fname in os.listdir(POSTS_DIR):
        if fname.endswith(".md"):
            try:
                with open(os.path.join(POSTS_DIR, fname), encoding="utf-8") as f:
                    content = f.read()
                    match = re.search(r'source:\s*"(.*?)"', content)
                    if match:
                        links.append(match.group(1))
            except Exception as e:
                print(f"Error reading {fname}: {e}")
    return links

def get_manifest_url(item_url):
    """Convert LOC item URL to manifest URL."""
    if not item_url.endswith('/'):
        item_url += '/'
    return urljoin(item_url, 'manifest.json')

def download_images_from_manifest(manifest_url):
    """Download images from a IIIF manifest."""
    try:
        print(f"Fetching manifest: {manifest_url}")
        resp = requests.get(manifest_url, timeout=15)
        resp.raise_for_status()  # Raise exception for HTTP errors
        
        data = resp.json()
        
        # Handle different IIIF manifest structures
        canvases = []
        if "sequences" in data and data["sequences"]:
            canvases = data["sequences"][0].get("canvases", [])
        elif "items" in data:  # IIIF 3.0 format
            canvases = data["items"]
        
        if not canvases:
            print(f"No canvases found in manifest: {manifest_url}")
            return
        
        print(f"Found {len(canvases)} images to download")
        
        for i, canvas in enumerate(canvases):
            try:
                # Handle different manifest formats
                img_url = None
                
                # IIIF 2.x format
                if "images" in canvas and canvas["images"]:
                    img_info = canvas["images"][0].get("resource", {})
                    img_url = img_info.get("@id")
                
                # IIIF 3.0 format
                elif "items" in canvas and canvas["items"]:
                    body = canvas["items"][0].get("body", {})
                    img_url = body.get("id")
                
                if img_url:
                    # Generate filename
                    img_hash = hashlib.md5(img_url.encode()).hexdigest()[:10]
                    ext = os.path.splitext(img_url.split('?')[0])[-1] or ".jpg"  # Remove query params
                    img_path = os.path.join(IMAGES_DIR, f"{img_hash}{ext}")
                    
                    if not os.path.exists(img_path):
                        print(f"Downloading image {i+1}/{len(canvases)}: {img_url}")
                        
                        # Add headers to avoid being blocked
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (compatible; LOC Image Downloader)'
                        }
                        
                        img_resp = requests.get(img_url, headers=headers, timeout=30)
                        img_resp.raise_for_status()
                        
                        with open(img_path, "wb") as out_file:
                            out_file.write(img_resp.content)
                        
                        print(f"✓ Saved: {img_path}")
                        
                        # Be respectful - add small delay
                        time.sleep(0.5)
                    else:
                        print(f"✓ Already exists: {img_path}")
                else:
                    print(f"No image URL found for canvas {i+1}")
                    
            except Exception as e:
                print(f"Error downloading image {i+1}: {e}")
                continue
                
    except requests.exceptions.RequestException as e:
        print(f"Network error fetching manifest {manifest_url}: {e}")
    except Exception as e:
        print(f"Error processing manifest {manifest_url}: {e}")

if __name__ == "__main__":
    print("Starting LOC image download...")
    
    item_links = extract_source_links()
    print(f"Found {len(item_links)} source links")
    
    loc_links = [link for link in item_links if "loc.gov/item" in link]
    print(f"Found {len(loc_links)} LOC item links")
    
    if not loc_links:
        print("No LOC links found in posts!")
    
    for i, link in enumerate(loc_links):
        print(f"\nProcessing link {i+1}/{len(loc_links)}: {link}")
        manifest_url = get_manifest_url(link)
        download_images_from_manifest(manifest_url)
    
    print(f"\n✅ Finished! Check the '{IMAGES_DIR}' directory for downloaded images.")
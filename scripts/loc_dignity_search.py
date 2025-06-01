import requests, hashlib, time, os
import psycopg2
from urllib.parse import quote
from datetime import datetime

BASE_URL = "https://www.loc.gov/photos/?fo=json&q="

KEYWORDS = [
    "slavery", "enslaved people", "slave", "plantation", "African Americans",
    "freedmen", "reconstruction", "emancipation", "civil rights", "abolition",
    "underground railroad", "black history", "negro", "colored people",
    "jim crow", "segregation"
]

DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT", 5432),
}

def hash_url(url): return hashlib.md5(url.encode()).hexdigest()[:10]

def fetch_items(keyword, max_pages=2):
    results = []
    for page in range(1, max_pages + 1):
        url = f"{BASE_URL}{quote(keyword)}&sp={page}"
        try:
            print(f"Fetching: {url}")
            res = requests.get(url, timeout=30)
            res.raise_for_status()
            page_results = res.json().get("results", [])
            results.extend(page_results)
            time.sleep(2)
        except Exception as e:
            print(f"Error fetching {keyword} page {page}: {e}")
            break
    return results

def insert_into_db(items, keyword):
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            for item in items:
                title = item.get("title")
                url = item.get("url")
                thumb = item.get("image", {}).get("full") or ""
                loc_id = hash_url(url)

                cur.execute("""
                    INSERT INTO loc_items (id, keyword, title, url, thumbnail, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING;
                """, (loc_id, keyword, title, url, thumb, datetime.utcnow()))
        conn.commit()
        print(f"Inserted {len(items)} items for '{keyword}'")

if __name__ == "__main__":
    for kw in KEYWORDS:
        data = fetch_items(kw, max_pages=2)
        insert_into_db(data, kw)

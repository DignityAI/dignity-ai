from flask import Flask, jsonify
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os

app = Flask(__name__)

# Base LOC Search URL
BASE_URL = "https://www.loc.gov/collections/?q="

# Safe keyword list
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

# Setup requests session with retries
session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)

def fetch_loc_data(keyword, page=1):
    try:
        url = f"{BASE_URL}{requests.utils.quote(keyword)}&sp={page}&fo=json"
        response = session.get(url, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@app.route("/")
def index():
    return "✅ Library of Congress Content Fetcher is running."

@app.route("/fetch/<keyword>")
def fetch_keyword(keyword):
    if keyword not in KEYWORDS:
        return jsonify({"error": "❌ Keyword not in allowed list"}), 400
    data = fetch_loc_data(keyword)
    return jsonify(data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

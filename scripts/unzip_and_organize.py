import os
import zipfile
import json

INPUT_DIR = "datasets"   # Where ZIPs are downloaded
OUTPUT_DIR = "output"    # Where MD files go

def unzip_all():
    for file in os.listdir(INPUT_DIR):
        if file.endswith(".zip"):
            path = os.path.join(INPUT_DIR, file)
            with zipfile.ZipFile(path, 'r') as zip_ref:
                extract_folder = os.path.join(INPUT_DIR, file[:-4])
                os.makedirs(extract_folder, exist_ok=True)
                zip_ref.extractall(extract_folder)
                print(f"Extracted {file} to {extract_folder}")

def json_to_md(json_path, state_code):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Example: extract bill summaries from JSON keys (adjust based on actual structure)
    md_lines = []
    if "bills" in data:
        for bill_id, bill in data["bills"].items():
            title = bill.get("title", "No Title")
            session = bill.get("session", "Unknown Session")
            status = bill.get("status", {}).get("statusname", "Unknown Status")
            md_lines.append(f"### Bill {bill_id}: {title}\n")
            md_lines.append(f"- Session: {session}\n")
            md_lines.append(f"- Status: {status}\n\n")
    else:
        md_lines.append("No bills data found.\n")

    state_folder = os.path.join(OUTPUT_DIR, state_code)
    os.makedirs(state_folder, exist_ok=True)
    md_file = os.path.join(state_folder, os.path.basename(json_path).replace('.json', '.md'))

    with open(md_file, 'w', encoding='utf-8') as md_f:
        md_f.writelines(md_lines)
    print(f"Created Markdown summary: {md_file}")

def main():
    unzip_all()
    # Walk through extracted folders and convert JSON to MD
    for root, dirs, files in os.walk(INPUT_DIR):
        for file in files:
            if file.endswith(".json"):
                # Infer state code from folder name (customize if needed)
                parts = root.split(os.sep)
                state_code = "IL"  # As example for Illinois only, or extract dynamically
                json_path = os.path.join(root, file)
                json_to_md(json_path, state_code)

if __name__ == "__main__":
    main()

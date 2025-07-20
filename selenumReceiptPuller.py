import os
import time
import re
import shutil
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# === CONFIG ===
CSV_FILE = "/Users/jspodick/Documents/GitHub/Uber-Receipts/UberReceipts_July.csv"
DOWNLOAD_DIR = os.path.abspath("/Users/jspodick/Desktop/CT_UberReceipts")

# Create the download folder if it doesn't exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# === Set up Chrome options ===
chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
    "plugins.always_open_pdf_externally": True
})
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--user-data-dir='/Users/jspodick/Library/Application Support/Google/Chrome'")
chrome_options.add_argument("--profile-directory=Profile 1")


# Optional: for headless mode, uncomment this
# chrome_options.add_argument("--headless=new")

# === Start browser ===
driver = webdriver.Chrome(options=chrome_options)
driver.get("https://business.uber.com")

input("🔐 Log into Uber Business, then press Enter to continue...")

# === Load CSV ===
df = pd.read_csv(CSV_FILE)

def sanitize_filename(s):
    return re.sub(r'[^\w\-_.]', '_', s)

def wait_for_new_download(before_files, timeout=60, stable_wait=2):
    start_time = time.time()
    last_seen = Nonelast_mod_time = None
    last_mod_time = None

    while time.time() - start_time < timeout:
        current_files = os.listdir(DOWNLOAD_DIR)
        new_files = list(set(current_files) - set(before_files))

        for fname in new_files:
            full_path = os.path.join(DOWNLOAD_DIR, fname)

            if fname.startswith('.'):
                continue

            if not fname.lower().endswith('.pdf'):
                continue

            # Check for stability
            mod_time = os.path.getmtime(full_path)
            if fname == last_seen and mod_time == last_mod_time:
                # File hasn't changed, assume it's fully downloaded
                return fname

            last_seen = fname
            last_mod_time = mod_time

        time.sleep(stable_wait)
    return None

for i, row in df.iterrows():
    url = row["Receipt"]
    last_name = sanitize_filename(str(row["Last Name"]))
    timestamp_raw = str(row["Transaction Timestamp (UTC)"])

    try:
        # Format timestamp
        ts = datetime.fromisoformat(timestamp_raw.replace("Z", ""))
        timestamp_str = ts.strftime("%Y-%m-%d_%H-%M-%S")
    except Exception:
        timestamp_str = sanitize_filename(timestamp_raw)

    base_filename = f"{last_name}_{timestamp_str}.pdf"

    print(f"📥 [{i+1}/{len(df)}] Downloading: {base_filename}")

    # Track downloads
    before_files = os.listdir(DOWNLOAD_DIR)

    # Visit receipt link
    driver.get(url)

    # Wait for file to download
    downloaded_file = wait_for_new_download(before_files)

    if downloaded_file:
        old_path = os.path.join(DOWNLOAD_DIR, downloaded_file)
        new_path = os.path.join(DOWNLOAD_DIR, base_filename)

        try:
            os.rename(old_path, new_path)
            print(f"✅ Saved: {base_filename}")
        except FileNotFoundError:
            print(f"⚠️ File disappeared before renaming: {old_path}")
    else:
        print(f"⚠️ Timeout waiting for download: {url}")

driver.quit()
print("🎉 All downloads complete.")


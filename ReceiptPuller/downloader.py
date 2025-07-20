# downloader.py
import os
import time
import re
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import subprocess
import tempfile
import shutil
import pickle
from tkinter import messagebox, Tk


def save_cookies(driver, path):
    with open(path, "wb") as f:
        pickle.dump(driver.get_cookies(), f)

def load_cookies(driver, path):
    with open(path, "rb") as f:
        cookies = pickle.load(f)
        for cookie in cookies:
            # Only add cookies for business.uber.com or subdomain-less cookies
            if "domain" in cookie and "business.uber.com" not in cookie["domain"]:
                continue
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                print(f"⚠️ Failed to load cookie: {cookie.get('name', '')} — {e}")


def chrome_is_running():
    try:
        output = subprocess.check_output(["pgrep", "-f", "Google Chrome"])
        return bool(output.strip())
    except subprocess.CalledProcessError:
        return False

def sanitize_filename(s):
    return re.sub(r'[^\w\-_.]', '_', str(s))

def wait_for_new_download(before_files, download_dir, timeout=60, stable_wait=2):
    start_time = time.time()
    last_seen = None
    last_mod_time = None

    while time.time() - start_time < timeout:
        current_files = os.listdir(download_dir)
        new_files = list(set(current_files) - set(before_files))

        for fname in new_files:
            full_path = os.path.join(download_dir, fname)

            if fname.startswith('.') or not fname.lower().endswith('.pdf'):
                continue

            mod_time = os.path.getmtime(full_path)
            if fname == last_seen and mod_time == last_mod_time:
                return fname

            last_seen = fname
            last_mod_time = mod_time

        time.sleep(stable_wait)

    return None

def run_download(csv_path, download_dir, update_progress=None, is_cancelled=None):
    # Load CSV
    df = pd.read_csv(csv_path)
    cookie_file = os.path.join(os.path.expanduser("~"), ".uber_business_cookies.pkl")

    import tempfile
    import shutil

    temp_profile_dir = tempfile.mkdtemp()

    # Setup Chrome with user profile (adjust profile path if needed)
    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={temp_profile_dir}")
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": os.path.abspath(download_dir),
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True
    })
    chrome_options.add_argument("--start-maximized")

    chromedriver_path = os.path.join(os.path.dirname(__file__), 'chromedriver')
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get("https://business.uber.com")

    # Load cookies if available
    if os.path.exists(cookie_file):
        print("🍪 Loading saved cookies...")
        driver.get("https://business.uber.com")  # domain must be loaded before adding cookies
        load_cookies(driver, cookie_file)
        driver.refresh()
    else:
        # Create a simple popup window
        root = Tk()
        root.withdraw()  # Hide the main tkinter window
        messagebox.showinfo("Login Required", "Please log into Uber Business in the opened browser window.\n\nOnce logged in, click OK to continue.")
        root.destroy()

        save_cookies(driver, cookie_file)
        print("✅ Cookies saved for future sessions.")


    for i, row in df.iterrows():
        if is_cancelled and is_cancelled():
            print("Download cancelled by user.")
            break

        url = row.get("Receipt")
        last_name = sanitize_filename(row.get("Last Name", f"user{i}"))
        timestamp_raw = str(row.get("Transaction Timestamp (UTC)", "unknown"))

        try:
            ts = datetime.fromisoformat(timestamp_raw.replace("Z", ""))
            timestamp_str = ts.strftime("%Y-%m-%d_%H-%M-%S")
        except Exception:
            timestamp_str = sanitize_filename(timestamp_raw)

        filename = f"{last_name}_{timestamp_str}.pdf"
        print(f"📥 [{i+1}/{len(df)}] Downloading: {filename}")

        if update_progress:
            update_progress(i + 1, len(df))

        before_files = os.listdir(download_dir)

        driver.get(url)

        downloaded_file = wait_for_new_download(before_files, download_dir)
        if downloaded_file:
            old_path = os.path.join(download_dir, downloaded_file)
            new_path = os.path.join(download_dir, filename)

            try:
                os.rename(old_path, new_path)
                print(f"✅ Saved: {filename}")
            except FileNotFoundError:
                print(f"⚠️ File disappeared before renaming: {old_path}")
        else:
            print(f"⚠️ Timeout waiting for download: {url}")

    driver.quit()
    shutil.rmtree(temp_profile_dir, ignore_errors=True)
    print("🎉 All downloads complete.")

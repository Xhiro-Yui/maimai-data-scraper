import os
import io
import sys
import zipfile
import requests
import chromedriver_autoinstaller

from selenium import webdriver
from .driver_utils import get_driver_path_folder


def create_chrome_driver():
    # Try to make Chrome less detectable
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    options.add_argument(f'user-agent={user_agent}')

    folder = get_driver_path_folder()
    prop_file = os.path.join(folder, "chromedriver.properties")

    chrome_version = chromedriver_autoinstaller.get_chrome_version()
    if not chrome_version:
        raise RuntimeError("❌ Chrome not found.")
    print(f"✅ Chrome version: {chrome_version}")

    latest_meta = requests.get(
        "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"
    ).json()
    latest_version = latest_meta["channels"]["Stable"]["version"]
    print(f"📦 Required driver version: {latest_version}")

    props = {}
    if os.path.exists(prop_file):
        with open(prop_file) as pf:
            for line in pf:
                if '=' in line:
                    k, v = line.strip().split('=', 1)
                    props[k] = v

    current = props.get("version")
    current_path = props.get("driver_path")
    if current == latest_version and current_path and os.path.exists(current_path):
        print("✅ Using cached ChromeDriver")
        return webdriver.Chrome(service=webdriver.chrome.service.Service(current_path), options=options)

    print("🌐 Downloading ChromeDriver...")
    downloads = latest_meta["channels"]["Stable"]["downloads"]["chromedriver"]
    dl = next((d for d in downloads if "win" in d["platform"]), None)
    if not dl:
        raise RuntimeError("❌ No Windows ChromeDriver available.")

    zip_bytes = requests.get(dl["url"]).content
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        folder_name = zf.namelist()[0].split('/')[0]
        zf.extractall(folder)
        path = os.path.join(folder, folder_name, "chromedriver.exe")
        if not os.path.exists(path):
            raise RuntimeError("❌ Driver extraction failed.")

    with open(prop_file, "w") as pf:
        pf.write(f"version={latest_version}\n")
        pf.write(f"driver_path={path}\n")

    print("✅ ChromeDriver ready.")
    return webdriver.Chrome(service=webdriver.chrome.service.Service(path), options=options)

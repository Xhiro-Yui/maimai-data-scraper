import io
import logging
import os
import zipfile

import chromedriver_autoinstaller
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver

from scraper.resources.resource_manager import resources
from scraper.utils.path_resolver import resolve_app_file_path

logger = logging.getLogger(__name__.split(".")[-1])


def get_installed_chrome_version() -> str:
    """
    Detect the installed Chrome version on the current machine.

    :return: Chrome version string, e.g. "126.0.6478.127"
    :raises RuntimeError: if Chrome is not found
    """
    version = chromedriver_autoinstaller.get_chrome_version()
    if not version:
        raise RuntimeError("❌ Chrome not found on this machine.")
    logger.info(f"Installed Chrome version on machine: {version}")
    return version


def ensure_chromedriver(version: str) -> str:
    """
    Ensure a ChromeDriver exists for the given Chrome version.
    If cached version is available, reuse it. Otherwise, download from
    Google’s Chrome-for-Testing repository.

    :param version: Chrome version string
    :return: Path to the ChromeDriver executable
    :raises RuntimeError: if ChromeDriver cannot be downloaded
    """
    prop_file = resolve_app_file_path("chromedriver.properties")
    folder = os.path.dirname(prop_file)

    # Load existing metadata
    props = {}
    if os.path.exists(prop_file):
        with open(prop_file) as pf:
            for line in pf:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    props[k] = v

    cached_version = props.get("version")
    cached_path = props.get("driver_path")
    if cached_version == version and cached_path and os.path.exists(cached_path):
        logger.info(f"Matching ChromeDriver {cached_version} detected.")
        return cached_path

    logger.info("Matching ChromeDriver version not found.")
    logger.info(f"Downloading ChromeDriver for version {version}.")

    latest_meta = requests.get(
        "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"
    ).json()

    downloads = latest_meta["channels"]["Stable"]["downloads"]["chromedriver"]
    dl = next((d for d in downloads if "win" in d["platform"]), None)
    if not dl:
        raise RuntimeError("No Windows ChromeDriver available for version: " + version)

    zip_bytes = requests.get(dl["url"]).content
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        folder_name = zf.namelist()[0].split("/")[0]
        zf.extractall(folder)
        driver_path = os.path.join(folder, folder_name, "chromedriver.exe")
        if not os.path.exists(driver_path):
            raise RuntimeError("Driver extraction failed.")

    with open(prop_file, "w") as pf:
        pf.write(f"version={version}\n")
        pf.write(f"driver_path={driver_path}\n")

    logger.info(f"ChromeDriver {version} ready.")
    return driver_path


def get_chrome_driver() -> WebDriver:
    """
    Create and return a Selenium Chrome WebDriver with anti-detection tweaks.
    Ensures a valid ChromeDriver is available.

    :return: selenium.webdriver.remote.webdriver.WebDriver
    """
    chrome_version = get_installed_chrome_version()
    driver_path = ensure_chromedriver(chrome_version)

    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    )
    if resources.config.logging_level != "DEBUG":  # Only prints Chromium logs if debugging
        logger.info("Suppressing Chrome logs")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument("--log-level=3")

    return webdriver.Chrome(service=Service(driver_path), options=options)

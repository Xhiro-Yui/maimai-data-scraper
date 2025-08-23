import sys

from .chrome_driver import create_chrome_driver


class BrowserDriver:



def initialize_driver(config):
    browser = config.get("BROWSER", "headless").strip().lower()
    if browser not in ["chrome", "firefox", "headless"]:
        print("BROWSER should be one of the following: chrome, firefox, headless")
        sys.exit(1)

    if browser == "chrome":
        driver = create_chrome_driver()
    elif browser == "firefox":
        # driver = create_firefox_driver()
        print("Firefox currently not supported! Please check back in the future")
        sys.exit(1)
    else:
        # driver = create_headless_driver()
        print("Headless currently not supported! Please check back in the future")
        sys.exit(1)

    return driver

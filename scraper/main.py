import threading

from scraper.exception.terminate_exception import Terminate

# Patch PyCharm debugger bug (uses old Thread.isAlive method)
if not hasattr(threading.Thread, "isAlive"):
    threading.Thread.isAlive = threading.Thread.is_alive

import logging
import sys

from scraper.constants import Browser
from scraper.driver.chrome_driver import get_chrome_driver
from scraper.exception.scraper_exception import ScraperError
from scraper.resources.resource_manager import resources
from scraper.scrapers.browser_scraper import BrowserScraper

logger = logging.getLogger(__name__.split(".")[-1])

if __name__ == "__main__":
    try:
        if resources.config["BROWSER"].lower() == Browser.CHROME:
            logger.info("Its chrome")
            scraper = BrowserScraper(resources.config, resources.database, get_chrome_driver())
            scraper.scrape()

        if resources.config["BROWSER"].lower() == Browser.FIREFOX:
            logger.info("firefox")
        if resources.config["BROWSER"].lower() == Browser.CHROMIUM:
            logger.info("Its chromium")
    except ScraperError as e:
        logger.error(e)
        input("Press Enter to exit...")
        sys.exit(1)
    except Terminate:
        input("Press Enter to exit...")
        sys.exit(1)

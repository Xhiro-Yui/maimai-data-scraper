import threading

# Patch PyCharm debugger bug (uses old Thread.isAlive method)
if not hasattr(threading.Thread, "isAlive"):
    threading.Thread.isAlive = threading.Thread.is_alive

import logging
import sys

from scraper.constants import Browser
from scraper.exception.scraper_exception import ScraperError
from scraper.resources.models import PlayData
from scraper.resources.resource_manager import resource

if __name__ == "__main__":
    try:
        # Do nothing
        if resource.config["BROWSER"].lower() == Browser.CHROME:
            logging.info("Its chrome")
            # scraper = BrowserScraper(resource.config, resource.database, None)
            # scraper.scrape()
            data = PlayData(idx="1,12345", title="Fake song", difficulty="13+")
            resource.database.insert_new_play_data(data)

        if resource.config["BROWSER"].lower() == Browser.FIREFOX:
            logging.info("firefox")
        if resource.config["BROWSER"].lower() == Browser.CHROMIUM:
            logging.info("Its chromium")
    except ScraperError as e:
        logging.error(e)
        input("Press Enter to exit...")
        sys.exit(1)

    # Start scraping

    # Configure basic logging
    # Log messages with level DEBUG or higher will be shown

    # To show only INFO messages and above in production:
    # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # if config.get("BROWSER") == "headless":
    #     print("Headless mode")
    #     headless_scrape()
    # else:
    #     browser_scrape(config, initialize_driver(config))

# main.py or scraper/config.py for config

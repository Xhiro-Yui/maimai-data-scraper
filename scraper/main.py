from scrape_browser import browser_scrape
from scrape_headless import headless_scrape
from setup import *
from setup.drivers.init_driver import initialize_driver


def initialize_scraper():
    """
    Initializes required files such as `config.env` and `.db` file
    :return:
    """
    ensure_config_exists()
    initialize_database()
    return load_config()


if __name__ == "__main__":
    config = initialize_scraper()

    if config.get("BROWSER") == "headless":
        print("Headless mode")
        headless_scrape()
    else:
        browser_scrape(config, initialize_driver(config))

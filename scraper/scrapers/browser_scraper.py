import logging

from selenium.webdriver.remote.webdriver import WebDriver

from scraper.constants import Endpoints
from scraper.scrapers.scraper import Scraper


class BrowserScraper(Scraper):
    def __init__(self, config, database, driver: WebDriver):
        """
        Browser-agnostic scraper using Selenium WebDriver.

        Args:
            config (Config): App configuration.
            database (Database): Database connection instance.
            driver (WebDriver): Any Selenium WebDriver instance (Chrome, Firefox, headless, etc.)
        """
        self.config = config
        self.database = database
        self.driver = driver

    def scrape(self) -> None:
        logging.info(f"BrowserScraper started scraping using {type(self.driver).__name__}")
        url = Endpoints.LOGIN_PAGE
        logging.info("BrowserScraper finished scraping. " + url)
        # self.driver.get(url)

        # TODO: parse the page and store results in database
        logging.info("BrowserScraper finished scraping.")

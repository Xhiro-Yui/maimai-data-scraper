import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from scraper.constants import Endpoints
from scraper.exception.terminate_exception import Terminate
from scraper.resources.i18n.messages import Messages
from scraper.resources.resource_manager import t
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
        logging.info(
            f"Scraper using [{self.driver.capabilities["browserName"]} {self.driver.capabilities["browserVersion"]}]")

    def scrape(self) -> None:
        self.driver.get(Endpoints.LOGIN_PAGE)

        maintenance_dom = self.get_element_if_exists(By.CLASS_NAME, "main_info")
        if maintenance_dom:
            self._exit(t(Messages.Error.SERVER_UNDER_MAINTENANCE))
        else:
            self._exit(t(Messages.Error.CHROME_NOT_FOUND))

        logging.info("BrowserScraper finished scraping.")

    def _exit(self, exit_reason: str) -> None:
        logging.info(f"Exiting due to : {exit_reason}")
        self.driver.quit()
        raise Terminate()

    def get_element_if_exists(self, by, selector):
        elements = self.driver.find_elements(by, selector)
        return elements[0] if elements else None
    # def login(driver, config):
    #     driver.get("")
    #     wait_delay = config.get("UI_WAIT_DELAY", 10)
    #     wait_timeout = config.get("UI_WAIT_TIMEOUT", 60)
    #     print(f"Wait delay : {wait_delay} | wait timeout : {wait_timeout}")
    #
    #     print("Clicking the TOS checkbox...")
    #     # Check the TOS checkbox
    #     tos_checkbox = WebDriverWait(driver, wait_timeout).until(
    #         EC.element_to_be_clickable((By.ID, "agree-maimaidxex"))
    #     )
    #     tos_checkbox.click()
    #     time.sleep(wait_delay / 4)
    #
    #     print("Clicking the SEGA ID login button...")
    #     # Click the SEGA ID login button
    #     segaid_button = WebDriverWait(driver, wait_timeout).until(
    #         EC.element_to_be_clickable((By.CLASS_NAME, "c-button--openid--segaId"))
    #     )
    #     segaid_button.click()
    #     time.sleep(wait_delay)
    #
    #     print("Looking for the login id and password area...")
    #     # Wait for hidden form to show
    #     WebDriverWait(driver, wait_timeout).until(
    #         EC.visibility_of_element_located((By.ID, "sid"))
    #     )
    #     time.sleep(wait_delay)
    #     WebDriverWait(driver, wait_timeout).until(
    #         EC.visibility_of_element_located((By.ID, "password"))
    #     )
    #
    #     print("Inputting login id and password ...")
    #     driver.find_element(By.ID, "sid").clear()
    #     driver.find_element(By.ID, "sid").send_keys(config.get("USERNAME", ""))
    #     time.sleep(wait_delay / 4)
    #     driver.find_element(By.ID, "password").clear()
    #     driver.find_element(By.ID, "password").send_keys(config.get("PASSWORD", ""))
    #     time.sleep(wait_delay / 4)
    #
    #     driver.find_element(By.ID, "btnSubmit").click()
    #
    #     # Wait for successful login (redirect to home)
    #     WebDriverWait(driver, wait_timeout).until(
    #         EC.url_contains("/maimai-mobile/home/")
    #     )
    #     print("Login successful!")

import logging
import os
import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from scraper.constants import Endpoints
from scraper.exception.terminate_exception import Terminate
from scraper.resources.database_schema import SONG_DATA_TABLE
from scraper.resources.i18n.messages import Messages
from scraper.resources.models import SongData
from scraper.resources.resource_manager import t
from scraper.scrapers.scraper import Scraper
from scraper.utils.scraping_utils import identify_song_type


class BrowserScraper(Scraper):
    def __init__(self, config, database, driver: WebDriver):
        """
        Browser-agnostic scraper using Selenium WebDriver. Configuration, database and driver is externalized

        Args:
            config (Config): App configuration.
            database (Database): Database connection instance.
            driver (WebDriver): Any Selenium WebDriver instance (Chrome, Firefox, headless, etc.)
        """
        self.config = config
        self.database = database
        self.driver = driver
        self.wait_delay = self.config.get_int("UI_WAIT_DELAY", 5)
        self.wait_timeout = self.config.get_int("UI_WAIT_TIMEOUT", 15)

        logging.info(
            f"Scraper using [{self.driver.capabilities["browserName"]} {self.driver.capabilities["browserVersion"]}]")
        logging.debug(f"Wait delay : {self.wait_delay} | wait timeout : {self.wait_timeout}")

    def scrape(self) -> None:
        try:
            # self.login()
            self.get_song_scores()
            self.get_latest_records()

            logging.info("BrowserScraper finished scraping.")
        except Exception as e:
            logging.error(f"Exception occurred {e}")
            self._exit(t(Messages.Error.UNEXPECTED_ERROR))

    def _exit(self, exit_reason: str) -> None:
        logging.info(f"Exiting due to : {exit_reason}")
        self.driver.quit()
        raise Terminate()

    def get_element_if_exists(self, by, selector):
        elements = self.driver.find_elements(by, selector)
        return elements[0] if elements else None

    def login(self) -> bool:
        """
        Reminder : Always sleep awhile before doing any page interaction to make it less bot-like
        :return: True if login success
        """
        self.driver.get(Endpoints.LOGIN_PAGE)

        maintenance_dom = self.get_element_if_exists(By.CLASS_NAME, "main_info")
        if maintenance_dom:
            self._exit(t(Messages.Error.SERVER_UNDER_MAINTENANCE))

        logging.debug("Clicking the TOS checkbox...")
        # Check the TOS checkbox
        tos_checkbox = WebDriverWait(self.driver, self.wait_timeout).until(
            ec.element_to_be_clickable((By.ID, "agree-maimaidxex"))
        )
        time.sleep(self.wait_delay // 4)
        tos_checkbox.click()

        logging.debug("Clicking the SEGA ID login button...")
        # Click the SEGA ID login button
        sega_id_button = WebDriverWait(self.driver, self.wait_timeout).until(
            ec.element_to_be_clickable((By.CLASS_NAME, "c-button--openid--segaId"))
        )
        time.sleep(self.wait_delay // 4)
        sega_id_button.click()

        WebDriverWait(self.driver, self.wait_timeout).until(
            ec.visibility_of_element_located((By.ID, "sid"))
        )
        WebDriverWait(self.driver, self.wait_timeout).until(
            ec.visibility_of_element_located((By.ID, "password"))
        )

        logging.debug("Inputting login id and password ...")
        time.sleep(self.wait_delay // 4)
        self.driver.find_element(By.ID, "sid").clear()
        self.driver.find_element(By.ID, "sid").send_keys(self.config["USERNAME"])
        time.sleep(self.wait_delay / 4)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(self.config["PASSWORD"])

        time.sleep(self.wait_delay / 4)
        self.driver.find_element(By.ID, "btnSubmit").click()

        return self.check_login_success()

    def check_login_success(self) -> bool:
        try:
            # Wait for redirect to home page
            WebDriverWait(self.driver, self.wait_timeout).until(
                ec.url_contains("/maimai-mobile/home/")
            )
            logging.info("Login successful.")
            return True
        except TimeoutException:
            # Timeout waiting for home page. Did log in fail?
            error_dom = self.get_element_if_exists(By.ID, "error")
            if error_dom:
                logging.info(f"Login failed :  {error_dom.text}")
                return False
            return False

    def get_song_scores(self):
        # self.get_song_scores_by_difficulty("basic")
        # self.get_song_scores_by_difficulty("advanced")
        # self.get_song_scores_by_difficulty("expert")
        self.get_song_scores_by_difficulty("master")
        # self.get_song_scores_by_difficulty("remaster")
        # self.get_song_scores_by_difficulty("utage")

    def get_song_scores_by_difficulty(self, difficulty: str) -> None:
        html_path = os.path.abspath(f"scraper/mock/song_scores_{difficulty}.html")
        file_url = f"file:///{html_path.replace(os.sep, '/')}"  # Windows-safe
        self.driver.get(file_url)
        songs_dom = self.driver.find_elements(By.CLASS_NAME, f"music_{difficulty}_score_back")
        for song_dom in songs_dom:
            song_title = song_dom.find_element(By.CLASS_NAME, "music_name_block")
            song_type = song_dom.find_element(By.XPATH, "..").find_element(By.CLASS_NAME,
                                                                           "music_kind_icon").get_attribute("src")
            score = song_dom.find_elements(By.CLASS_NAME, "music_score_block")

            entity: SongData = self.database.find(SONG_DATA_TABLE,
                                                  SongData(
                                                      song_title=song_title.text,
                                                      song_type=identify_song_type(song_type)
                                                  ),
                                                  SongData)
            if entity:
                # TODO : Handle dont exists (never played before)
                setattr(entity, f"score_{difficulty}", score[0].text)
                setattr(entity, f"dx_score_{difficulty}", score[1].text)
                self.database.upsert(SONG_DATA_TABLE, entity)
            else:
                song_data = SongData(
                    song_title=song_title.text,
                    song_type=identify_song_type(song_type)
                )
                setattr(song_data, f"score_{difficulty}", score[0].text)
                setattr(song_data, f"dx_score_{difficulty}", score[1].text)
                self.database.upsert(SONG_DATA_TABLE, entity)

    def get_latest_records(self):
        pass

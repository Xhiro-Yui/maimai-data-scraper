import logging
import os
import time
from dataclasses import replace
from typing import Optional

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from scraper.constants import Endpoints
from scraper.exception.terminate_exception import Terminate
from scraper.resources.database_schema import SONG_DATA_TABLE, PLAY_DATA_TABLE
from scraper.resources.i18n.messages import Messages
from scraper.resources.models import SongData, PlayData
from scraper.resources.resource_manager import t, resources
from scraper.scrapers.scraper import Scraper
from scraper.utils import scraping_utils as su

logger = logging.getLogger(__name__.split(".")[-1])


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

        logger.info(
            f"Scraper using [{self.driver.capabilities["browserName"]} {self.driver.capabilities["browserVersion"]}]")
        logger.debug(f"Wait delay : {self.wait_delay} | wait timeout : {self.wait_timeout}")

    def scrape(self) -> None:
        try:
            # self.login()
            # self.get_song_scores()
            self.get_latest_records()

            logger.info("BrowserScraper finished scraping.")
        except Exception as e:
            logger.error(f"Exception occurred {e}")
            self._exit(t(Messages.Error.UNEXPECTED_ERROR))

    def _exit(self, exit_reason: str) -> None:
        logger.info(f"Exiting due to : {exit_reason}")
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

        logger.debug("Clicking the TOS checkbox...")
        # Check the TOS checkbox
        tos_checkbox = WebDriverWait(self.driver, self.wait_timeout).until(
            ec.element_to_be_clickable((By.ID, "agree-maimaidxex"))
        )
        time.sleep(self.wait_delay // 4)
        tos_checkbox.click()

        logger.debug("Clicking the SEGA ID login button...")
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

        logger.debug("Inputting login id and password ...")
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
            logger.info("Login successful.")
            return True
        except TimeoutException:
            # Timeout waiting for home page. Did log in fail?
            error_dom = self.get_element_if_exists(By.ID, "error")
            if error_dom:
                logger.info(f"Login failed :  {error_dom.text}")
                return False
            return False

    def get_song_scores(self):
        # self.get_song_scores_by_difficulty("basic")
        # self.get_song_scores_by_difficulty("advanced")
        # self.get_song_scores_by_difficulty("expert")
        # self.get_song_scores_by_difficulty("master")
        # self.get_song_scores_by_difficulty("remaster")
        # self.get_song_scores_by_difficulty("utage")
        pass

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

            entity: SongData = self.database.select(SONG_DATA_TABLE,
                                                    SongData(
                                                        song_title=song_title.text,
                                                        song_type=su.identify_song_type(song_type)
                                                    ),
                                                    SongData, 1)
            if entity:
                # TODO : Handle dont exists (never played before)
                setattr(entity, f"score_{difficulty}", score[0].text)
                setattr(entity, f"dx_score_{difficulty}", score[1].text)
                self.database.upsert(SONG_DATA_TABLE, entity)
            else:
                song_data = SongData(
                    song_title=song_title.text,
                    song_type=su.identify_song_type(song_type)
                )
                setattr(song_data, f"score_{difficulty}", score[0].text)
                setattr(song_data, f"dx_score_{difficulty}", score[1].text)
                self.database.upsert(SONG_DATA_TABLE, entity)

    def get_latest_records(self):
        html_path = os.path.abspath("scraper/mock/records.html")
        file_url = f"file:///{html_path.replace(os.sep, '/')}"
        self.driver.get(file_url)
        records_dom = self.driver.find_elements(By.CLASS_NAME, "playlog_top_container")
        available_idx = []
        new_idx = []
        for playlog_top_dom in records_dom:
            playlog_song_container = (
                playlog_top_dom
                .find_element(By.XPATH, "..")
                .find_elements(By.XPATH, "./*")[1]
            )
            idx = su.find_element_attribute(playlog_song_container, By.XPATH, ".//form/input[@name='idx']", "value")
            available_idx.append(idx)
            if not self.database.check_if_play_data_exists(idx):
                new_idx.append(idx)
                play_data = PlayData(
                    idx=idx,
                    title=su.parse_song_title(playlog_song_container.find_element(By.CSS_SELECTOR, ".basic_block")),
                    difficulty=su.find_element_attribute(playlog_song_container, By.CSS_SELECTOR, ".playlog_level_icon",
                                                         "text"),
                    track=su.find_element_attribute(playlog_top_dom, By.CSS_SELECTOR, ".sub_title span", "text", 0),
                    music_type=su.parse_chart_type(
                        su.find_element_attribute(playlog_song_container, By.CLASS_NAME, "playlog_music_kind_icon",
                                                  "src")
                    ),
                    new_achievement=bool(
                        playlog_song_container.find_elements(By.CSS_SELECTOR, ".playlog_achievement_newrecord")),
                    achievement=su.find_element_attribute(playlog_song_container, By.CSS_SELECTOR,
                                                          ".playlog_achievement_txt", "text"),
                    rank=su.parse_rank(
                        su.find_element_attribute(playlog_song_container, By.CSS_SELECTOR, ".playlog_scorerank", "src")
                    ),
                    new_dx_score=bool(
                        playlog_song_container.find_elements(By.CSS_SELECTOR, ".playlog_deluxscore_newrecord")),
                    dx_score=su.find_element_attribute(playlog_song_container, By.CSS_SELECTOR,
                                                       ".playlog_score_block .white", "text"),
                    dx_stars=su.parse_dx_stars(
                        su.find_element_attribute(playlog_song_container, By.CSS_SELECTOR,
                                                  ".playlog_score_block .playlog_deluxscore_star", "src")
                    ),
                    combo_status=su.parse_combo(
                        su.find_element_attribute(playlog_song_container, By.CSS_SELECTOR,
                                                  ".playlog_result_innerblock img", "src", -2)
                    ),
                    sync_status=su.parse_sync(
                        su.find_element_attribute(playlog_song_container, By.CSS_SELECTOR,
                                                  ".playlog_result_innerblock img", "src", -1)
                    ),
                    place=su.parse_placement(
                        playlog_song_container.find_elements(By.CSS_SELECTOR, ".playlog_matching_icon")
                    ),
                    played_at=su.find_element_attribute(playlog_top_dom, By.CSS_SELECTOR, ".sub_title span", "text", 1),
                    detailed=False,
                    play_data_version=resources.play_data_version
                )
                self.database.upsert(PLAY_DATA_TABLE, play_data)
        if new_idx:
            logger.info("New records found. Appending details")
            self._parse_song_details(new_idx)
        # Additional loop to add details if for some reason it didn't get detailed
        for idx in available_idx:
            play_data: PlayData = self.database.select(PLAY_DATA_TABLE, {"idx": idx}, PlayData)
            if not play_data.detailed:
                logger.info("Orphaned records found with details still available found. Appending details")
                self._parse_song_details([idx], play_data)

    def _parse_song_details(self, new_idx: list[str], optional_data: Optional[PlayData] = None) -> None:
        for idx in reversed(new_idx):
            # endpoint = Endpoints.RECORD_DETAILS(idx)
            html_path = os.path.abspath("scraper/mock/record_details.html")
            file_url = f"file:///{html_path.replace(os.sep, '/')}"
            # Delay between page loading
            self.driver.get(file_url)
            time.sleep(self.wait_delay)

            # Fetch the existing entity for updates
            if optional_data:
                play_data = optional_data
            else:
                play_data: PlayData = self.database.select(PLAY_DATA_TABLE, {"idx": idx}, PlayData)

            if play_data:
                details_dom = self.driver.find_elements(By.CLASS_NAME, "gray_block")[0]

                tap_selector = ".playlog_notes_detail tr:nth-child(2) td"
                hold_selector = ".playlog_notes_detail tr:nth-child(3) td"
                slide_selector = ".playlog_notes_detail tr:nth-child(4) td"
                touch_selector = ".playlog_notes_detail tr:nth-child(5) td"
                break_selector = ".playlog_notes_detail tr:nth-child(6) td"
                combo_string = su.find_element_attribute(details_dom, By.CSS_SELECTOR, ".playlog_score_block > div",
                                                         "text", 0)
                combo = combo_string.split("/")[0] if "/" in combo_string else combo_string
                max_combo = combo_string.split("/")[1] if "/" in combo_string else combo_string
                sync_string = su.find_element_attribute(details_dom, By.CSS_SELECTOR, ".playlog_score_block > div",
                                                        "text", 1)
                sync = sync_string.split("/")[0] if "/" in sync_string else sync_string
                max_sync = sync_string.split("/")[1] if "/" in sync_string else sync_string
                play_data = replace(
                    play_data,
                    fast=su.find_element_attribute(details_dom, By.CSS_SELECTOR, ".playlog_fl_block div div", "text",
                                                   0),
                    late=su.find_element_attribute(details_dom, By.CSS_SELECTOR, ".playlog_fl_block div div", "text",
                                                   1),
                    tap_critical=su.find_element_attribute(details_dom, By.CSS_SELECTOR, tap_selector, "text", 0),
                    tap_perfect=su.find_element_attribute(details_dom, By.CSS_SELECTOR, tap_selector, "text", 1),
                    tap_great=su.find_element_attribute(details_dom, By.CSS_SELECTOR, tap_selector, "text", 2),
                    tap_good=su.find_element_attribute(details_dom, By.CSS_SELECTOR, tap_selector, "text", 3),
                    tap_miss=su.find_element_attribute(details_dom, By.CSS_SELECTOR, tap_selector, "text", 4),
                    hold_critical=su.find_element_attribute(details_dom, By.CSS_SELECTOR, hold_selector, "text", 0),
                    hold_perfect=su.find_element_attribute(details_dom, By.CSS_SELECTOR, hold_selector, "text", 1),
                    hold_great=su.find_element_attribute(details_dom, By.CSS_SELECTOR, hold_selector, "text", 2),
                    hold_good=su.find_element_attribute(details_dom, By.CSS_SELECTOR, hold_selector, "text", 3),
                    hold_miss=su.find_element_attribute(details_dom, By.CSS_SELECTOR, hold_selector, "text", 4),
                    slide_critical=su.find_element_attribute(details_dom, By.CSS_SELECTOR, slide_selector, "text", 0),
                    slide_perfect=su.find_element_attribute(details_dom, By.CSS_SELECTOR, slide_selector, "text", 1),
                    slide_great=su.find_element_attribute(details_dom, By.CSS_SELECTOR, slide_selector, "text", 2),
                    slide_good=su.find_element_attribute(details_dom, By.CSS_SELECTOR, slide_selector, "text", 3),
                    slide_miss=su.find_element_attribute(details_dom, By.CSS_SELECTOR, slide_selector, "text", 4),
                    touch_critical=su.find_element_attribute(details_dom, By.CSS_SELECTOR, touch_selector, "text", 0),
                    touch_perfect=su.find_element_attribute(details_dom, By.CSS_SELECTOR, touch_selector, "text", 1),
                    touch_great=su.find_element_attribute(details_dom, By.CSS_SELECTOR, touch_selector, "text", 2),
                    touch_good=su.find_element_attribute(details_dom, By.CSS_SELECTOR, touch_selector, "text", 3),
                    touch_miss=su.find_element_attribute(details_dom, By.CSS_SELECTOR, touch_selector, "text", 4),
                    break_critical=su.find_element_attribute(details_dom, By.CSS_SELECTOR, break_selector, "text", 0),
                    break_perfect=su.find_element_attribute(details_dom, By.CSS_SELECTOR, break_selector, "text", 1),
                    break_great=su.find_element_attribute(details_dom, By.CSS_SELECTOR, break_selector, "text", 2),
                    break_good=su.find_element_attribute(details_dom, By.CSS_SELECTOR, break_selector, "text", 3),
                    break_miss=su.find_element_attribute(details_dom, By.CSS_SELECTOR, break_selector, "text", 4),
                    combo=combo,
                    max_combo=max_combo,
                    sync=sync,
                    max_sync=max_sync,
                    detailed=True
                )
                self.database.upsert(PLAY_DATA_TABLE, play_data)

            else:
                logger.error(f"Play data for {idx} not found in database")

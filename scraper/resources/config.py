import logging
import os
import sys
import textwrap

from dotenv import dotenv_values

from scraper.exception.scraper_exception import ScraperError
from scraper.utils.path_resolver import resolve_app_file_path

logger = logging.getLogger(__name__.split(".")[-1])


class Config:
    def __init__(self, filename: str = "config.env"):
        # Load only from .env file (ignores system env)
        config_path = resolve_app_file_path(filename)

        logger.info("Checking if existing config exists...")
        if not os.path.exists(config_path):
            self._generate_default_config_file(config_path)
        else:
            logger.info("Config exists. Loading config values.")
        self._values = dotenv_values(config_path)

        # Validate required values
        self._validate_config()

    def _validate_config(self):
        try:
            valid_browsers = ["chrome", "firefox", "chromium", "headless"]
            valid_region = ["jp", "japan", "intl", "international"]

            # Check required fields
            username = self.get("USERNAME").strip()
            password = self.get("PASSWORD").strip()
            browser = self.get("BROWSER").strip().lower()
            region = self.get("REGION").strip().lower()

            missing_fields = []
            if not username:
                missing_fields.append("USERNAME")
            if not password:
                missing_fields.append("PASSWORD")
            if not browser:
                missing_fields.append("BROWSER")
            if browser.lower() not in (b.lower() for b in valid_browsers):  # Case in-sensitive
                raise ScraperError(f"Invalid BROWSER value: '{browser}'. Must be one of {valid_browsers}")
            if region.lower() not in (r.lower() for r in valid_region):  # Case in-sensitive
                raise ScraperError(f"Invalid REGION value: '{region}'. Must be one of {valid_region}")
            if missing_fields:
                raise ScraperError(f"Missing required config values: {', '.join(missing_fields)}")
        except ScraperError as e:
            logger.error(e)
            input("Press Enter to exit...")
            sys.exit(1)

    def get(self, key: str, default=None) -> str:
        if key in self._values:
            return self._values[key]

        if default is not None:
            return default

        raise Exception(f"Missing required config: {key}")

    def get_int(self, key: str, default: int = None) -> int:
        value = self.get(key, default)
        return int(value)

    @property
    def logging_level(self) -> str:
        return self.get("LOGGING").upper()

    def __getitem__(self, key: str):
        return self._values[key]

    def __contains__(self, key: str):
        return key in self._values

    def __repr__(self):
        return f"Config({self._values})"

    @staticmethod
    def _generate_default_config_file(config_path: str) -> None:
        default_config = textwrap.dedent("""\
        USERNAME=
        PASSWORD=
        BROWSER=
        REGION=
        LANGUAGE=en

        ### Do not touch the section below unless you know what you are doing
        
        CHECK_INTERVAL_MINUTES=5
        LOGGING=INFO
        UI_WAIT_DELAY=5
        UI_WAIT_TIMEOUT=15

        # These credentials are stored locally only.
        # They are never sent anywhere except to log in to maimai website
        # REGION should be one of the following: jp, japan, intl, international
        # BROWSER should be one of the following: chrome, firefox, headless
        # LANGUAGE should be one of the following: en, ja
        """)

        logger.info("No existing config found. Creating default config file.")
        with open(config_path, "w") as f:
            f.write(default_config)
        logger.info(f"First-time setup: '{os.path.abspath(config_path)}' has been created.")
        logger.info("Please open it and fill in your USERNAME, PASSWORD, and BROWSER.")
        input("Press Enter to exit...")
        sys.exit(1)

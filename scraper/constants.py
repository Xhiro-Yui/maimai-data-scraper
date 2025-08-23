class File:
    """File and directory paths."""
    DATABASE_NAME: str = "maimai_data.db"
    LOG_FILE: str = "scraper.log"
    CONFIG_FILE: str = "config.env"


class Browser:
    """Supported browsers for Selenium."""
    CHROME: str = "chrome"
    FIREFOX: str = "firefox"
    CHROMIUM: str = "chromium"
    SUPPORTED = [CHROME, FIREFOX, CHROMIUM]
    DEFAULT: str = CHROMIUM


class Logging:
    """Logging-related constants."""
    DEFAULT_LEVEL: str = "INFO"
    LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    LOG_FORMAT = "%(asctime)s - %(levelname)5s - %(message)s"


class Endpoints:
    LOGIN_PAGE: str
    LOGOUT_PAGE: str
    HOME_PAGE: str

    # Define all endpoints per region
    _REGIONS = {
        "INTL": {
            "LOGIN_PAGE": "https://www.google.com",
            "LOGOUT_PAGE": "https://www.google.com/logout",
            "HOME_PAGE": "https://www.google.com/home"
        },
        "JP": {
            "LOGIN_PAGE": "https://www.google.co.jp",
            "LOGOUT_PAGE": "https://www.google.co.jp/logout",
            "HOME_PAGE": "https://www.google.co.jp/home"
        }
    }

def load_endpoints(region: str):
    """
    Dynamically attach endpoints for the selected region to the Endpoints class.
    """
    region_upper = region.upper()
    current = Endpoints._REGIONS.get(region_upper)
    if current is None:
        raise ValueError(f"Unknown REGION: {region}")

    for key, value in current.items():
        setattr(Endpoints, key, value)
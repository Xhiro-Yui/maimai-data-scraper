class File:
    DATABASE_NAME: str = "maimai_data.db"
    LOG_FILE: str = "scraper.log"
    CONFIG_FILE: str = "config.env"


class Browser:
    CHROME: str = "chrome"
    FIREFOX: str = "firefox"
    CHROMIUM: str = "chromium"
    SUPPORTED = [CHROME, FIREFOX, CHROMIUM]
    DEFAULT: str = CHROMIUM


class Logging:
    DEFAULT_LEVEL: str = "INFO"
    LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    LOG_FORMAT = "%(asctime)s - %(levelname)5s - %(message)s"


class Endpoints:
    LOGIN_PAGE: str
    PLAYER_DATA: str
    RECORDS: str
    SONG_SCORES_BASIC: str
    SONG_SCORES_ADVANCED: str
    SONG_SCORES_EXPERT: str
    SONG_SCORES_MASTER: str
    SONG_SCORES_REMASTER: str
    SONG_SCORES_UTAGE: str

    # Define all endpoints per region
    _REGIONS = {
        "INTL": {
            "LOGIN_PAGE": "https://maimaidx-eng.com/maimai-mobile/login/",
            "PLAYER_DATA": "https://maimaidx-eng.com/maimai-mobile/playerData/",
            "RECORDS": "https://maimaidx-eng.com/maimai-mobile/record/",
            "SONG_SCORES_BASIC": "https://maimaidx-eng.com/maimai-mobile/record/musicGenre/search/?genre=99&diff=0",
            "SONG_SCORES_ADVANCED": "https://maimaidx-eng.com/maimai-mobile/record/musicGenre/search/?genre=99&diff=1",
            "SONG_SCORES_EXPERT": "https://maimaidx-eng.com/maimai-mobile/record/musicGenre/search/?genre=99&diff=2",
            "SONG_SCORES_MASTER": "https://maimaidx-eng.com/maimai-mobile/record/musicGenre/search/?genre=99&diff=3",
            "SONG_SCORES_REMASTER": "https://maimaidx-eng.com/maimai-mobile/record/musicGenre/search/?genre=99&diff=4",
            "SONG_SCORES_UTAGE": "https://maimaidx-eng.com/maimai-mobile/record/musicGenre/search/?genre=99&diff=10"
        },
        "JP": {
            "LOGIN_PAGE": "https://maimaidx-eng.com/maimai-mobile/login/",
            "PLAYER_DATA": "https://maimaidx-eng.com/maimai-mobile/playerData/",
            "RECORDS": "https://maimaidx-eng.com/maimai-mobile/record/",
            "SONG_SCORES_BASIC": "https://maimaidx-eng.com/maimai-mobile/record/musicGenre/search/?genre=99&diff=0",
            "SONG_SCORES_ADVANCED": "https://maimaidx-eng.com/maimai-mobile/record/musicGenre/search/?genre=99&diff=1",
            "SONG_SCORES_EXPERT": "https://maimaidx-eng.com/maimai-mobile/record/musicGenre/search/?genre=99&diff=2",
            "SONG_SCORES_MASTER": "https://maimaidx-eng.com/maimai-mobile/record/musicGenre/search/?genre=99&diff=3",
            "SONG_SCORES_REMASTER": "https://maimaidx-eng.com/maimai-mobile/record/musicGenre/search/?genre=99&diff=4",
            "SONG_SCORES_UTAGE": "https://maimaidx-eng.com/maimai-mobile/record/musicGenre/search/?genre=99&diff=10"
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

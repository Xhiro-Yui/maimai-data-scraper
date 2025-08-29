import atexit
import logging

from scraper.constants import File, load_endpoints, Logging
from scraper.metadata.metadata_manager import MetadataManager
from scraper.resources.config import Config
from scraper.resources.database import Database
from scraper.resources.i18n.messages import Messages

logging.basicConfig(
    level=logging.INFO,
    format=Logging.LOG_FORMAT
)  # Default, so first run also has logs

logger = logging.getLogger(__name__.split(".")[-1])


class ResourceManager:
    """
    Centralized resource manager for global singletons (Config, Database, etc.)
    """

    def __init__(self):
        # Load config first
        self.config = Config()

        # Update the default logging based on config value
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.logging_level.upper()))
        logging.getLogger("selenium").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

        # Initialize other resources
        logger.debug("Initializing database.")
        self.database = Database(File.DATABASE_NAME)
        logger.debug("Database initialization complete")

        self._lang_class = getattr(Messages, self.config["LANGUAGE"].upper(), Messages.EN)
        load_endpoints(self.config["REGION"])

        self._metadata = MetadataManager(self.database)
        logger.info("ResourceManager setup complete")

    def get_message(self, key: str) -> str:
        value = getattr(self._lang_class, key, None)

        if value is not None:
            return value

        # Missing in target language, fallback to English
        fallback_value = getattr(Messages.EN, key, key)

        # Log a warning
        logger.warning(
            f"Missing translation for key '{key}' in language '{self._lang_class.__name__}', using fallback."
        )

        return fallback_value

    def shutdown(self) -> None:
        if self.database is not None:
            try:
                logger.debug(f"Shutting down {File.DATABASE_NAME}")
                self.database.close_connection()

            except Exception as e:
                logger.error(f"Error while closing database: {e}")

        logger.debug("Shut down complete!")

    @property
    def play_data_version(self):
        return self._metadata.version.play_data_version


resources = ResourceManager()
atexit.register(resources.shutdown)


def t(key: str) -> str:
    return resources.get_message(key)

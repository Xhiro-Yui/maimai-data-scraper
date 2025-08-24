import atexit
import json
import logging

from scraper.constants import File, load_endpoints
from scraper.resources.config import Config
from scraper.resources.database import Database
from scraper.resources.i18n.messages import Messages
from scraper.utils.path_resolver import resolve_app_file_path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)5s] %(name)s: %(message)s"
)  # Default, so first run also has logs


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

        # Initialize other resources
        logging.debug("Initializing database.")
        self.database = Database(File.DATABASE_NAME)
        logging.debug("Database initialization complete")

        self._lang_class = getattr(Messages, self.config["LANGUAGE"].upper(), Messages.EN)
        load_endpoints(self.config["REGION"])
        logging.info("ResourceManager setup complete")

    def get_message(self, key: str) -> str:
        return getattr(self._lang_class, key, getattr(Messages.EN, key, key))

    def shutdown(self) -> None:
        if self.database is not None:
            try:
                logging.debug(f"Shutting down {File.DATABASE_NAME}")
                self.database.close_connection()

            except Exception as e:
                logging.error(f"Error while closing database: {e}")

        logging.debug("Shut down complete!")


resources = ResourceManager()
atexit.register(resources.shutdown)


def t(key: str) -> str:
    return resources.get_message(key)

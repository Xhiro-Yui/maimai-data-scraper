import atexit
import logging

from scraper.constants import File, load_endpoints
from scraper.resources.config import Config
from scraper.resources.database import Database

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
        logging.debug("Initialization complete")

        load_endpoints(self.config.get("REGION"))

    def shutdown(self):
        if self.database is not None:
            try:
                logging.debug(f"Shutting down {File.DATABASE_NAME}")
                self.database.close_connection()

            except Exception as e:
                logging.error(f"Error while closing database: {e}")

        logging.debug("Shut down complete!")


resource = ResourceManager()

atexit.register(resource.shutdown)

import logging
from dataclasses import asdict

from scraper.resources.database import Database
from scraper.resources.database_schema import METADATA_TABLE
from scraper.resources.models import Metadata

logger = logging.getLogger(__name__)


class VersionMetadata:
    def __init__(self, row: Metadata):
        for key, value in asdict(row).items():
            if key != "id":  # skip PK
                setattr(self, key, value)


class MetadataManager:
    # To be updated
    SCRAPER_VERSION = "1.0.0"

    # To be updated when MaiMai website data changes
    PLAY_DATA_VERSION = 1

    # Data stored versions
    # When the scraper changes the data structure
    # Should be rarely used
    DATABASE_VERSION = 1

    def __init__(self, database: Database):
        self.database = database
        self._initialize_update_metadata()
        self.version = self._load_cache()
        self._validate_schema()

    def _validate_schema(self):
        # For future use
        pass

    def get_metadata(self, key: str) -> int:
        """
        Main method to retrieve version data from DB
        :param key:
        :return:
        """

    def _load_cache(self) -> VersionMetadata:
        """Load all metadata into memory"""
        metadata: Metadata = self.database.select(METADATA_TABLE, {}, entity_class=Metadata, limit=1)
        return VersionMetadata(metadata)

    def _initialize_update_metadata(self):
        entity: Metadata = Metadata(
            id=1,
            scraper_version=self.SCRAPER_VERSION,
            play_data_version=self.PLAY_DATA_VERSION,
            database_version=self.DATABASE_VERSION
        )
        self.database.upsert(METADATA_TABLE, entity)

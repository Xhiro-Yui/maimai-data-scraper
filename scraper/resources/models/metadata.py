from dataclasses import dataclass


@dataclass
class Metadata:
    scraper_version: str = None
    database_version: str = None

from dataclasses import dataclass
from typing import Optional


@dataclass
class Metadata:
    id: Optional[int] = None
    scraper_version: str = None
    database_version: str = None
    play_data_version: str = None

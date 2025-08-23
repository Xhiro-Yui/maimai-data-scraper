from dataclasses import dataclass
from typing import Optional


@dataclass
class PlayerData:
    id: Optional[int] = None
    total_plays: int = None

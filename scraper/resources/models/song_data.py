from dataclasses import dataclass
from typing import Optional


@dataclass
class SongData:
    id: Optional[int] = None
    song_title: str = None
    song_type: str = None
    score_basic: Optional[str] = None
    dx_score_basic: Optional[str] = None
    score_advanced: Optional[str] = None
    dx_score_advanced: Optional[str] = None
    score_expert: Optional[str] = None
    dx_score_expert: Optional[str] = None
    score_master: Optional[str] = None
    dx_score_master: Optional[str] = None
    score_remaster: Optional[str] = None
    dx_score_remaster: Optional[str] = None

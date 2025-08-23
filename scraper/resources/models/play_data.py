from dataclasses import dataclass
from typing import Optional


@dataclass
class PlayData:
    id: Optional[int] = None
    idx: str = None
    title: str = None
    difficulty: str = None
    music_type: Optional[str] = None
    track: Optional[str] = None
    place: Optional[str] = None
    played_at: Optional[str] = None
    achievement: Optional[str] = None
    score: Optional[str] = None
    dx_stars: Optional[int] = None
    rank: Optional[str] = None
    fc_status: Optional[str] = None
    sync_status: Optional[str] = None
    max_combo: Optional[str] = None
    max_sync: Optional[str] = None
    fast: Optional[int] = None
    late: Optional[int] = None
    tap_detail: Optional[str] = None
    hold_detail: Optional[str] = None
    slide_detail: Optional[str] = None
    touch_detail: Optional[str] = None
    break_detail: Optional[str] = None
    new_achievement: Optional[bool] = None
    new_dx_score: Optional[bool] = None

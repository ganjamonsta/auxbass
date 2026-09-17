from datetime import datetime
from typing import Dict, Optional, List
from pydantic import BaseModel

from api.schemas.tracks import TrackResponse


class LibraryStatsResponse(BaseModel):
    """Library statistics"""
    total_tracks: int
    total_duration_seconds: int
    album_count: int
    artist_count: int
    by_source: Dict[str, int]


class LibrarySyncStats(BaseModel):
    """Compact stats for sync check"""
    total_tracks: int
    artist_count: int
    album_count: int


class LibrarySyncStateResponse(BaseModel):
    """Library sync state for client background polling & live refresh"""
    total_tracks: int
    last_track_id: Optional[int] = None
    last_added_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None
    updated_tracks: List[TrackResponse] = []
    stats: Optional[LibrarySyncStats] = None

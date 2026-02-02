"""
TG Player API v2 - Library Schemas
"""
from typing import Dict, Optional
from pydantic import BaseModel


class LibraryStatsResponse(BaseModel):
    """Library statistics"""
    total_tracks: int
    total_duration_seconds: int
    album_count: int
    artist_count: int
    by_source: Dict[str, int]
    enrichment: Dict[str, int]

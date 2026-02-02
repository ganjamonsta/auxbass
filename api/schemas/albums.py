"""
TG Player API v2 - Album Schemas
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from .common import PaginatedResponse
from .tracks import TrackResponse


class AlbumTracklistItem(BaseModel):
    """Single track in full album tracklist"""
    track_number: int
    title: str
    artist: str = ""
    duration: int = 0  # seconds
    deezer_id: Optional[int] = None
    
    # Status in user's library
    in_library: bool = False
    track_id: Optional[int] = None  # Track ID if in library
    track: Optional[TrackResponse] = None  # Full track data if in library


class AlbumResponse(BaseModel):
    """Album response"""
    id: int
    name: str
    artist: str
    cover_url: Optional[str] = None
    release_date: Optional[str] = None  # YYYY-MM-DD string
    track_count: int = 0  # Tracks in user's library
    total_tracks: Optional[int] = None  # Total tracks in album (from Deezer)
    deezer_album_id: Optional[int] = None
    has_full_tracklist: bool = False  # Whether we have full tracklist data
    tags: Optional[List[str]] = None  # Tags from track enrichments or Last.fm

    class Config:
        from_attributes = True


class AlbumsListResponse(PaginatedResponse):
    """Paginated albums list"""
    items: List[AlbumResponse]


class AlbumDetailResponse(AlbumResponse):
    """Album with tracks and full tracklist for missing track display"""
    tracks: List[TrackResponse]  # Tracks in user's library
    full_tracklist: Optional[List[AlbumTracklistItem]] = None  # Complete album tracklist

"""
TG Player API v2 - Artist Schemas
"""
from typing import Optional, List
from pydantic import BaseModel

from .common import PaginatedResponse
from .albums import AlbumResponse
from .tracks import TrackResponse


class ArtistResponse(BaseModel):
    """Artist summary response"""
    name: str
    track_count: int
    album_count: int = 0
    cover_url: Optional[str] = None
    image_url: Optional[str] = None  # Alias for cover_url (frontend compat)
    latest_release_date: Optional[str] = None  # For sorting by date


class ArtistsListResponse(PaginatedResponse):
    """Paginated artists list"""
    items: List[ArtistResponse]


class ArtistDetailResponse(BaseModel):
    """Artist with albums and all tracks"""
    name: str
    track_count: int
    album_count: int
    cover_url: Optional[str] = None
    image_url: Optional[str] = None  # Alias for cover_url (frontend compat)
    albums: List[AlbumResponse] = []
    tracks: List[TrackResponse] = []  # All tracks by this artist

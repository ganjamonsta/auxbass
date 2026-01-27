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
    cover_url: Optional[str] = None


class ArtistsListResponse(PaginatedResponse):
    """Paginated artists list"""
    items: List[ArtistResponse]


class ArtistDetailResponse(BaseModel):
    """Artist with albums and top tracks"""
    name: str
    track_count: int
    album_count: int
    cover_url: Optional[str] = None
    albums: List[AlbumResponse] = []
    top_tracks: List[TrackResponse] = []

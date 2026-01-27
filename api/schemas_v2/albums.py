"""
TG Player API v2 - Album Schemas
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from .common import PaginatedResponse
from .tracks import TrackResponse


class AlbumResponse(BaseModel):
    """Album response"""
    id: int
    name: str
    artist: str
    cover_url: Optional[str] = None
    release_date: Optional[str] = None  # YYYY-MM-DD string
    track_count: int = 0
    deezer_album_id: Optional[int] = None

    class Config:
        from_attributes = True


class AlbumsListResponse(PaginatedResponse):
    """Paginated albums list"""
    items: List[AlbumResponse]


class AlbumDetailResponse(AlbumResponse):
    """Album with tracks"""
    tracks: List[TrackResponse]

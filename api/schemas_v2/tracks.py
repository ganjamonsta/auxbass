"""
TG Player API v2 - Track Schemas
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from .common import PaginatedResponse


class AlbumInfo(BaseModel):
    """Compact album info for track response"""
    id: int
    name: str
    cover_url: Optional[str] = None


class TrackResponse(BaseModel):
    """Track response"""
    id: int
    telegram_file_id: str
    title: str
    artist: Optional[str] = None
    duration: Optional[int] = None
    file_size: Optional[int] = None
    library_source: Optional[str] = None
    enrichment_status: Optional[str] = None
    
    # From enrichment
    album: Optional[AlbumInfo] = None
    cover_url: Optional[str] = None
    genre: Optional[str] = None
    release_date: Optional[str] = None  # YYYY-MM-DD string
    
    added_at: datetime

    class Config:
        from_attributes = True


class TracksListResponse(PaginatedResponse):
    """Paginated tracks list"""
    items: List[TrackResponse]


class TrackUpdate(BaseModel):
    """Track update request"""
    title: Optional[str] = None
    artist: Optional[str] = None


class TrackCreate(BaseModel):
    """Track create request (for API-based upload)"""
    telegram_file_id: str
    telegram_message_id: int
    title: str
    artist: Optional[str] = None
    duration: Optional[int] = None
    file_size: Optional[int] = None

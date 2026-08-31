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
    artist: Optional[str] = None  # Album artist (may differ from track artist for remixes/compilations)
    cover_url: Optional[str] = None


class TrackResponse(BaseModel):
    """Track response"""
    id: int
    telegram_file_id: str
    title: Optional[str] = None
    artist: Optional[str] = None
    file_name: Optional[str] = None  # Original filename for fallback display
    duration: Optional[int] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None  # audio/mpeg, audio/flac, etc.
    library_source: Optional[str] = None
    
    # Streaming compatibility
    is_streamable: bool = True  # False for HD formats (FLAC, WAV, etc.)
    streamable_id: Optional[int] = None  # MP3 alternative if this is HD
    hd_id: Optional[int] = None  # HD alternative if this is MP3
    
    # From enrichment
    album: Optional[AlbumInfo] = None
    album_name: Optional[str] = None  # Convenience field for backward compatibility
    cover_url: Optional[str] = None
    genre: Optional[str] = None
    tags: Optional[List[str]] = None  # Last.fm tags (detailed genres/styles)
    release_date: Optional[str] = None  # YYYY-MM-DD string
    
    # User library state
    is_liked: bool = False
    liked_at: Optional[datetime] = None
    play_count: int = 0
    in_library: Optional[bool] = None  # For global tracks: indicates if user has this track
    
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
    genre: Optional[str] = None  # Genre (stored in enrichment)


class TrackCreate(BaseModel):
    """Track create request (for API-based upload)"""
    telegram_file_id: str
    telegram_message_id: int
    title: str
    artist: Optional[str] = None
    duration: Optional[int] = None
    file_size: Optional[int] = None


class TrackLyricsResponse(BaseModel):
    """Track lyrics response"""
    track_id: int
    plain_lyrics: Optional[str] = None
    synced_lyrics: Optional[str] = None
    is_synced: bool = False
    is_instrumental: bool = False
    source: Optional[str] = None
    offset_ms: int = 0
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TrackLyricsUpdate(BaseModel):
    """Track lyrics update request"""
    plain_lyrics: Optional[str] = None
    synced_lyrics: Optional[str] = None
    is_instrumental: Optional[bool] = None
    offset_ms: Optional[int] = None


class TrackLyricsOffsetUpdate(BaseModel):
    """Track lyrics timing offset update request"""
    offset_ms: int


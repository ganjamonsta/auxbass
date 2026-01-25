"""Track-related schemas"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class TrackBase(BaseModel):
    """Base track schema with common fields"""
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None


class UploaderInfo(BaseModel):
    """Info about who uploaded the track"""
    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class ForwardSourceInfo(BaseModel):
    """Info about from whom the track was forwarded"""
    forward_from_id: Optional[int] = None
    forward_from_username: Optional[str] = None
    forward_from_name: Optional[str] = None
    forward_from_type: Optional[str] = None  # user, bot, channel
    
    class Config:
        from_attributes = True


class TrackResponse(TrackBase):
    """Full track response with all metadata"""
    id: int
    file_id: str
    duration: Optional[int] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    cover_url: Optional[str] = None
    enrichment_status: Optional[str] = None
    is_liked: bool = False
    is_unavailable: bool = False
    is_public: bool = True
    play_count: int = 0  # Global play count
    in_library: bool = False  # Is in current user's library
    uploader: Optional[UploaderInfo] = None  # Who uploaded
    forward_source: Optional[ForwardSourceInfo] = None  # Forwarded from
    created_at: datetime
    
    class Config:
        from_attributes = True


class TrackUpdate(BaseModel):
    """Schema for updating track metadata"""
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None
    is_public: Optional[bool] = None


class TracksListResponse(BaseModel):
    """Paginated list of tracks"""
    items: List[TrackResponse]
    total: int
    page: int
    per_page: int


class UserStatsResponse(BaseModel):
    """User statistics for the global library"""
    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    track_count: int = 0
    total_plays: int = 0
    
    class Config:
        from_attributes = True


class ArtistAlbumInfo(BaseModel):
    """Album info for artist card"""
    id: int
    name: str
    cover_url: Optional[str] = None
    track_count: int = 0
    release_date: Optional[str] = None  # YYYY-MM-DD format
    
    class Config:
        from_attributes = True


class ArtistDetailResponse(BaseModel):
    """Detailed artist info with tracks, albums and playlists"""
    name: str
    image_url: Optional[str] = None
    track_count: int = 0
    total_plays: int = 0
    tracks: List[TrackResponse] = []
    albums: List[ArtistAlbumInfo] = []
    playlists: List[ArtistAlbumInfo] = []  # Playlists containing this artist

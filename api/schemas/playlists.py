"""Playlist-related schemas"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from .tracks import TrackResponse


class PlaylistBase(BaseModel):
    """Base playlist schema"""
    name: str
    description: Optional[str] = None


class PlaylistCreate(PlaylistBase):
    """Schema for creating a playlist"""
    pass


class PlaylistUpdate(BaseModel):
    """Schema for updating a playlist"""
    name: Optional[str] = None
    description: Optional[str] = None


class PlaylistResponse(PlaylistBase):
    """Full playlist response"""
    id: int
    is_public: bool
    is_auto_album: bool = False
    is_auto_source: bool = False
    source_id: Optional[int] = None
    source_type: Optional[str] = None
    album_artist: Optional[str] = None  # Artist for album playlists
    cover_url: Optional[str] = None
    track_covers: List[str] = []  # Up to 4 unique track cover URLs for collage
    share_code: Optional[str]
    track_count: int = 0
    total_duration: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


class PlaylistWithTracksResponse(PlaylistResponse):
    """Playlist with embedded track list"""
    tracks: List[TrackResponse]


class AddTrackRequest(BaseModel):
    """Request to add track to playlist"""
    track_id: int
    position: Optional[int] = None


class AlbumCandidateResponse(BaseModel):
    """Potential album that can be auto-assembled"""
    artist: str
    album: str
    track_count: int
    total_duration: int
    cover_url: Optional[str] = None
    has_playlist: bool = False


class AssembleAlbumsResponse(BaseModel):
    """Response from album assembly"""
    created: int
    updated: int
    skipped: int
    albums: List[dict]

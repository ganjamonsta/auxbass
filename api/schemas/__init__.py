"""
TG Player API v2 - Schemas Module
"""
from .common import TelegramUser, PaginatedResponse, StatusResponse
from .tracks import (
    TrackResponse, TracksListResponse, TrackUpdate, TrackCreate,
    CoverSuggestion, SetCoverRequest
)
from .albums import AlbumResponse, AlbumsListResponse, AlbumDetailResponse
from .artists import ArtistResponse, ArtistsListResponse, ArtistDetailResponse, ArtistInfoResponse, ArtistTracksResponse
from .library import LibraryStatsResponse

__all__ = [
    # Common
    "TelegramUser",
    "PaginatedResponse",
    "StatusResponse",
    
    # Tracks
    "TrackResponse",
    "TracksListResponse",
    "TrackUpdate",
    "TrackCreate",
    "CoverSuggestion",
    "SetCoverRequest",
    
    # Albums
    "AlbumResponse",
    "AlbumsListResponse", 
    "AlbumDetailResponse",
    
    # Artists
    "ArtistResponse",
    "ArtistsListResponse",
    "ArtistDetailResponse",
    "ArtistInfoResponse",
    "ArtistTracksResponse",
    
    # Library
    "LibraryStatsResponse",
]

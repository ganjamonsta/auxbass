"""
Centralized Pydantic schemas for the API.
Organized by domain for easy imports.
"""

from .auth import (
    TelegramUser,
    AuthResult,
    CodeRequest,
    CodeVerify,
    CodeGenerated,
)

from .tracks import (
    TrackBase,
    TrackUpdate,
    TrackResponse,
    TracksListResponse,
    UploaderInfo,
    ForwardSourceInfo,
    UserStatsResponse,
    ArtistAlbumInfo,
    ArtistDetailResponse,
)

from .playlists import (
    PlaylistBase,
    PlaylistCreate,
    PlaylistUpdate,
    PlaylistResponse,
    PlaylistWithTracksResponse,
    AddTrackRequest,
    AlbumCandidateResponse,
    AssembleAlbumsResponse,
)

from .player import (
    StreamUrlResponse,
    DownloadPlaylistRequest,
)

__all__ = [
    # Auth
    "TelegramUser",
    "AuthResult",
    "CodeRequest",
    "CodeVerify",
    "CodeGenerated",
    # Tracks
    "TrackBase",
    "TrackUpdate",
    "TrackResponse",
    "TracksListResponse",
    "UploaderInfo",
    "ForwardSourceInfo",
    "UserStatsResponse",
    "ArtistAlbumInfo",
    "ArtistDetailResponse",
    # Playlists
    "PlaylistBase",
    "PlaylistCreate",
    "PlaylistUpdate",
    "PlaylistResponse",
    "PlaylistWithTracksResponse",
    "AddTrackRequest",
    "AlbumCandidateResponse",
    "AssembleAlbumsResponse",
    # Player
    "StreamUrlResponse",
    "DownloadPlaylistRequest",
]

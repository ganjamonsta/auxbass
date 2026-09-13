"""
TG Player API - External Service Schemas (SoundCloud, Spotify)

Pydantic models for external service items, shared between
ingestion and social routers.
"""
from typing import Optional, List
from pydantic import BaseModel


class ExternalAccountResponse(BaseModel):
    provider: str
    username: str
    display_name: Optional[str] = None
    profile_url: Optional[str] = None
    avatar_url: Optional[str] = None
    likes_count: int = 0
    tracks_count: int = 0
    connected: bool = True
    last_synced_at: Optional[str] = None
    show_on_profile: bool = True
    show_playlists: bool = True
    show_tracks: bool = True


class ExternalAccountPrivacyUpdate(BaseModel):
    show_on_profile: Optional[bool] = None
    show_playlists: Optional[bool] = None
    show_tracks: Optional[bool] = None


class SoundCloudLikeItem(BaseModel):
    url: str
    title: str
    artist: str
    duration: Optional[int] = None
    cover_url: Optional[str] = None
    genre: Optional[str] = None
    tags: Optional[List[str]] = None
    in_library: bool = False
    in_channel: bool = False
    already_in_tg: bool = False
    track_id: Optional[int] = None
    liked_at: Optional[str] = None
    created_at: Optional[str] = None
    track_number: Optional[int] = None


SoundCloudTrackItem = SoundCloudLikeItem


class SoundCloudPlaylistItem(BaseModel):
    id: str
    title: str
    permalink_url: str
    artwork_url: Optional[str] = None
    track_count: int = 0
    duration: Optional[int] = None
    author: str
    author_avatar: Optional[str] = None
    description: Optional[str] = None
    is_public: bool = True
    is_liked: bool = False
    created_at: Optional[str] = None


class UserLikesResponse(BaseModel):
    provider: str
    account: ExternalAccountResponse
    total_likes: int
    items: List[SoundCloudLikeItem]
    next_cursor: Optional[str] = None


class UserTracksResponse(BaseModel):
    provider: str
    account: ExternalAccountResponse
    total_tracks: int
    items: List[SoundCloudTrackItem]
    next_cursor: Optional[str] = None


class UserPlaylistsResponse(BaseModel):
    provider: str
    account: ExternalAccountResponse
    total_playlists: int
    items: List[SoundCloudPlaylistItem]
    next_cursor: Optional[str] = None


class PlaylistTracksResponse(BaseModel):
    provider: str
    playlist: SoundCloudPlaylistItem
    total_tracks: int
    tracks: List[SoundCloudTrackItem]


class ConnectAccountRequest(BaseModel):
    username_or_url: str
    auth_token: Optional[str] = None

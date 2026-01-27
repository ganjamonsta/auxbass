"""Player-related schemas for API v2"""

from typing import List
from pydantic import BaseModel


class StreamUrlResponse(BaseModel):
    """Response with streaming URL"""
    url: str  # Proxy URL, not direct Telegram URL
    expires_at: int
    track_id: int


class DownloadPlaylistRequest(BaseModel):
    """Request to download tracks via Telegram"""
    track_ids: List[int]
    playlist_name: str = "Плейлист"

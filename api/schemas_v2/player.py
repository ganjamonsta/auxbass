"""Player-related schemas for API v2"""

from typing import List, Optional
from pydantic import BaseModel


class StreamUrlResponse(BaseModel):
    """Response with streaming URL"""
    url: str  # Proxy URL, not direct Telegram URL
    expires_at: int
    track_id: int
    # HD track info (when playing MP3 but HD version exists)
    hd_track_id: Optional[int] = None
    hd_track_title: Optional[str] = None
    is_hd_available: bool = False


class DownloadPlaylistRequest(BaseModel):
    """Request to download tracks via Telegram"""
    track_ids: List[int]
    playlist_name: str = "Плейлист"

"""
TG Player API v2 - Common Schemas
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class TelegramUser(BaseModel):
    """Telegram user from auth"""
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    is_premium: Optional[bool] = None  # Telegram Premium status


class UserStatusResponse(BaseModel):
    """User status with premium features access"""
    user: "TelegramUser"
    has_channel: bool = False  # True if user connected backup channel
    can_save: bool = False  # True if user can save tracks, create playlists, etc.
    channel_info: Optional[dict] = None  # Channel details if connected


class PaginatedResponse(BaseModel):
    """Base for paginated responses"""
    total: int
    # Support both offset/limit and page/per_page
    offset: Optional[int] = None
    limit: Optional[int] = None
    page: Optional[int] = None
    per_page: Optional[int] = None


class StatusResponse(BaseModel):
    """Generic status response"""
    status: str
    message: Optional[str] = None

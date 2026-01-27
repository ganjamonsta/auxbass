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


class PaginatedResponse(BaseModel):
    """Base for paginated responses"""
    total: int
    page: int
    per_page: int


class StatusResponse(BaseModel):
    """Generic status response"""
    status: str
    message: Optional[str] = None

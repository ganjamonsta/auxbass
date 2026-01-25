"""Authentication schemas"""

from typing import Optional
from pydantic import BaseModel


class TelegramUser(BaseModel):
    """Telegram user data from initData"""
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: Optional[bool] = False
    photo_url: Optional[str] = None


class AuthResult(BaseModel):
    """Authentication result"""
    valid: bool
    user: Optional[TelegramUser] = None
    token: Optional[str] = None  # JWT token for browser auth


class CodeRequest(BaseModel):
    """Request for auth code"""
    user_id: int


class CodeVerify(BaseModel):
    """Verify auth code"""
    code: str


class CodeGenerated(BaseModel):
    """Generated auth code response (for bot)"""
    code: str
    expires_in: int  # seconds

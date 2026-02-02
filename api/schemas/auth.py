"""Authentication schemas for API v2"""

from typing import Optional
from pydantic import BaseModel


class AuthResult(BaseModel):
    """Authentication result"""
    valid: bool
    user: Optional["TelegramUser"] = None
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


# Import at end to avoid circular import
from api.schemas.common import TelegramUser
AuthResult.model_rebuild()

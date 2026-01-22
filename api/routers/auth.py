"""
TG Player API - Authentication
Validates Telegram Mini App initData
"""
import hmac
import hashlib
import json
from urllib.parse import parse_qsl, unquote
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.config import get_settings
from shared.database import get_session
from shared.models import User


router = APIRouter()
settings = get_settings()


class TelegramUser(BaseModel):
    """Telegram user data from initData"""
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: Optional[bool] = False


class AuthResult(BaseModel):
    """Authentication result"""
    valid: bool
    user: Optional[TelegramUser] = None


def validate_init_data(init_data: str, bot_token: str) -> Optional[dict]:
    """
    Validate Telegram Mini App initData
    Returns parsed data if valid, None otherwise
    """
    try:
        # Parse the init data
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        
        # Extract hash
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return None
        
        # Create data-check-string
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed.items())
        )
        
        # Create secret key using HMAC-SHA256
        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode("utf-8"),
            hashlib.sha256
        ).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        # Verify hash
        if calculated_hash != received_hash:
            return None
        
        # Check auth_date (optional: reject if too old)
        auth_date = int(parsed.get("auth_date", 0))
        now = int(datetime.utcnow().timestamp())
        if now - auth_date > 86400:  # 24 hours
            return None
        
        return parsed
        
    except Exception:
        return None


def parse_user_from_init_data(parsed_data: dict) -> Optional[TelegramUser]:
    """Extract user info from parsed init data"""
    user_json = parsed_data.get("user")
    if not user_json:
        return None
    
    try:
        user_data = json.loads(unquote(user_json))
        return TelegramUser(**user_data)
    except Exception:
        return None


async def get_current_user(
    x_telegram_init_data: str = Header(..., alias="X-Telegram-Init-Data")
) -> TelegramUser:
    """
    Dependency to get current user from Telegram initData
    """
    parsed = validate_init_data(x_telegram_init_data, settings.bot_token)
    
    if not parsed:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired Telegram init data"
        )
    
    user = parse_user_from_init_data(parsed)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Could not extract user from init data"
        )
    
    # Ensure user exists in database
    async with get_session() as session:
        db_user = await session.get(User, user.id)
        if not db_user:
            db_user = User(
                id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                is_premium=user.is_premium or False,
            )
            session.add(db_user)
    
    return user


@router.post("/validate", response_model=AuthResult)
async def validate_auth(
    x_telegram_init_data: str = Header(..., alias="X-Telegram-Init-Data")
):
    """Validate Telegram Mini App authentication"""
    parsed = validate_init_data(x_telegram_init_data, settings.bot_token)
    
    if not parsed:
        return AuthResult(valid=False)
    
    user = parse_user_from_init_data(parsed)
    return AuthResult(valid=True, user=user)


@router.get("/me", response_model=TelegramUser)
async def get_me(user: TelegramUser = Depends(get_current_user)):
    """Get current user info"""
    return user

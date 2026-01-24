"""
TG Player API - Authentication
Supports both Telegram Mini App initData and Telegram Login Widget (for browser PWA)
"""
import hmac
import hashlib
import json
from urllib.parse import parse_qsl, unquote
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
import jwt

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.config import get_settings
from shared.database import get_session
from shared.models import User


router = APIRouter()
settings = get_settings()


# ============== Models ==============

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


class TelegramLoginData(BaseModel):
    """Data from Telegram Login Widget"""
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str


# ============== JWT Functions ==============

def create_jwt_token(user: TelegramUser) -> str:
    """Create JWT token for browser authentication"""
    expire = datetime.utcnow() + timedelta(days=settings.jwt_expire_days)
    payload = {
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "photo_url": user.photo_url,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def verify_jwt_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ============== Telegram Mini App Auth ==============

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


# ============== Telegram Login Widget Auth ==============

def validate_telegram_login(data: dict, bot_token: str) -> bool:
    """
    Validate data from Telegram Login Widget
    https://core.telegram.org/widgets/login#checking-authorization
    """
    try:
        check_hash = data.pop("hash", None)
        if not check_hash:
            return False
        
        # Create data-check-string (sorted alphabetically)
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(data.items()) if v is not None
        )
        
        # Secret key is SHA256 hash of bot token
        secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        # Restore hash for later use
        data["hash"] = check_hash
        
        # Verify hash
        if calculated_hash != check_hash:
            return False
        
        # Check auth_date (reject if older than 1 day)
        auth_date = int(data.get("auth_date", 0))
        now = int(datetime.utcnow().timestamp())
        if now - auth_date > 86400:
            return False
        
        return True
        
    except Exception:
        return False


# ============== Unified Auth Dependency ==============

async def get_current_user(
    x_telegram_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    authorization: Optional[str] = Header(None),
) -> TelegramUser:
    """
    Dependency to get current user from either:
    1. Telegram Mini App initData (X-Telegram-Init-Data header)
    2. JWT token (Authorization: Bearer <token>)
    """
    
    # Try Telegram Mini App auth first
    if x_telegram_init_data:
        parsed = validate_init_data(x_telegram_init_data, settings.bot_token)
        if parsed:
            user = parse_user_from_init_data(parsed)
            if user:
                # Ensure user exists in database
                await ensure_user_in_db(user)
                return user
    
    # Try JWT auth
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        payload = verify_jwt_token(token)
        if payload:
            user = TelegramUser(
                id=payload["user_id"],
                first_name=payload.get("first_name", "User"),
                last_name=payload.get("last_name"),
                username=payload.get("username"),
                photo_url=payload.get("photo_url"),
            )
            return user
    
    raise HTTPException(
        status_code=401,
        detail="Authentication required. Use Telegram Mini App or login via browser."
    )


async def ensure_user_in_db(user: TelegramUser):
    """Ensure user exists in database, create if not"""
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


# ============== API Endpoints ==============

@router.post("/validate", response_model=AuthResult)
async def validate_auth(
    x_telegram_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    authorization: Optional[str] = Header(None),
):
    """
    Validate authentication and return user info.
    Works with both Telegram Mini App and JWT token.
    """
    # Try Telegram Mini App auth
    if x_telegram_init_data:
        parsed = validate_init_data(x_telegram_init_data, settings.bot_token)
        if parsed:
            user = parse_user_from_init_data(parsed)
            if user:
                await ensure_user_in_db(user)
                # Also return JWT token for potential browser use
                token = create_jwt_token(user)
                return AuthResult(valid=True, user=user, token=token)
    
    # Try JWT auth
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        payload = verify_jwt_token(token)
        if payload:
            user = TelegramUser(
                id=payload["user_id"],
                first_name=payload.get("first_name", "User"),
                last_name=payload.get("last_name"),
                username=payload.get("username"),
                photo_url=payload.get("photo_url"),
            )
            return AuthResult(valid=True, user=user, token=token)
    
    return AuthResult(valid=False)


@router.get("/me", response_model=TelegramUser)
async def get_me(user: TelegramUser = Depends(get_current_user)):
    """Get current user info"""
    return user


@router.post("/telegram-login", response_model=AuthResult)
async def telegram_login(data: TelegramLoginData):
    """
    Authenticate via Telegram Login Widget.
    Used for browser/PWA authentication.
    """
    # Convert to dict for validation
    login_data = {
        "id": data.id,
        "first_name": data.first_name,
        "auth_date": data.auth_date,
        "hash": data.hash,
    }
    if data.last_name:
        login_data["last_name"] = data.last_name
    if data.username:
        login_data["username"] = data.username
    if data.photo_url:
        login_data["photo_url"] = data.photo_url
    
    # Validate the login data
    if not validate_telegram_login(login_data.copy(), settings.bot_token):
        raise HTTPException(status_code=401, detail="Invalid Telegram login data")
    
    # Create user object
    user = TelegramUser(
        id=data.id,
        first_name=data.first_name,
        last_name=data.last_name,
        username=data.username,
        photo_url=data.photo_url,
    )
    
    # Ensure user in database
    await ensure_user_in_db(user)
    
    # Create JWT token
    token = create_jwt_token(user)
    
    return AuthResult(valid=True, user=user, token=token)


@router.get("/config")
async def get_auth_config():
    """
    Get authentication configuration for frontend.
    Returns bot username for Telegram Login Widget.
    """
    return {
        "bot_username": settings.bot_username,
        "telegram_login_enabled": bool(settings.bot_username),
    }


@router.post("/refresh", response_model=AuthResult)
async def refresh_token(user: TelegramUser = Depends(get_current_user)):
    """Refresh JWT token"""
    token = create_jwt_token(user)
    return AuthResult(valid=True, user=user, token=token)

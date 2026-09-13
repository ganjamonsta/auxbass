"""
TG Player API - Authentication
Supports Telegram Mini App initData and code-based browser auth
"""
import hmac
import hashlib
import json
import random
import string
from urllib.parse import parse_qsl, unquote
from typing import Optional
from datetime import datetime, timedelta, timezone

import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Header, Depends, Response, UploadFile, File
from pydantic import BaseModel
import jwt
from aiogram.types import BufferedInputFile

from shared.config import get_settings
from shared.database import get_session, get_db
from shared.models import User, UserChannel, utcnow
from api.schemas.common import TelegramUser, UserStatusResponse
from api.schemas.auth import (
    AuthResult,
    CodeRequest,
    CodeVerify,
    CodeGenerated,
)

logger = logging.getLogger(__name__)

AVATARS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "avatars"
AVATARS_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()
settings = get_settings()


# ============== In-Memory Auth Code Storage ==============
# Format: {code: {"user_id": int, "user_data": dict, "expires": datetime}}
auth_codes: dict = {}


# ============== JWT Functions ==============

def create_jwt_token(user: TelegramUser) -> str:
    """Create JWT token for browser authentication"""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_expire_days)
    payload = {
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "photo_url": user.photo_url,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
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
        now = int(datetime.now(timezone.utc).timestamp())
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


# ============== Code-Based Auth ==============

def generate_auth_code() -> str:
    """Generate 6-digit auth code"""
    return ''.join(random.choices(string.digits, k=6))


def cleanup_expired_codes():
    """Remove expired codes from storage"""
    now = datetime.now(timezone.utc)
    expired = [code for code, data in auth_codes.items() if data["expires"] < now]
    for code in expired:
        del auth_codes[code]


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
            await ensure_user_in_db(user)
            return user
    
    raise HTTPException(
        status_code=401,
        detail="Authentication required. Use Telegram Mini App or login via browser."
    )


async def get_optional_user(
    x_telegram_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    authorization: Optional[str] = Header(None),
) -> Optional[TelegramUser]:
    """
    Same as get_current_user but returns None instead of raising exception.
    Useful for endpoints that work for both authenticated and anonymous users.
    """
    
    # Try Telegram Mini App auth first
    if x_telegram_init_data:
        parsed = validate_init_data(x_telegram_init_data, settings.bot_token)
        if parsed:
            user = parse_user_from_init_data(parsed)
            if user:
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
            await ensure_user_in_db(user)
            return user
    
    return None


async def ensure_user_in_db(user: TelegramUser):
    """Ensure user exists in database, create if not, and populate customization fields"""
    async with get_session() as session:
        db_user = await session.get(User, user.id)
        if not db_user:
            db_user = User(
                id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                is_premium=user.is_premium or False,
                photo_url=user.photo_url,
            )
            session.add(db_user)
            await session.commit()
            await session.refresh(db_user)
        else:
            changed = False
            if user.username and db_user.username != user.username:
                db_user.username = user.username
                changed = True
            if user.first_name and db_user.first_name != user.first_name:
                db_user.first_name = user.first_name
                changed = True
            if user.last_name and db_user.last_name != user.last_name:
                db_user.last_name = user.last_name
                changed = True
            if user.photo_url and getattr(db_user, 'photo_url', None) != user.photo_url:
                db_user.photo_url = user.photo_url
                changed = True
            if changed:
                await session.commit()

        user.custom_nickname = db_user.custom_nickname
        user.custom_avatar_url = db_user.custom_avatar_url
        user.photo_url = getattr(db_user, 'photo_url', None) or user.photo_url
        user.hide_telegram_id = db_user.hide_telegram_id or False
        return db_user


# ============== Premium/Channel Check ==============

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def has_channel_connected(user_id: int, db: AsyncSession) -> bool:
    """
    Check if user has connected backup channel.
    Users with channel = premium features (save, library, playlists).
    """
    result = await db.execute(
        select(UserChannel.id).where(
            UserChannel.user_id == user_id,
            UserChannel.is_active == True
        )
    )
    return result.scalar_one_or_none() is not None


async def get_user_channel_info(user_id: int, db: AsyncSession) -> Optional[dict]:
    """Get user's channel info if connected"""
    result = await db.execute(
        select(UserChannel).where(
            UserChannel.user_id == user_id,
            UserChannel.is_active == True
        )
    )
    channel = result.scalar_one_or_none()
    if channel:
        return {
            "channel_id": channel.channel_id,
            "channel_username": channel.channel_username,
            "channel_title": channel.channel_title,
            "auto_forward": channel.auto_forward,
        }
    return None


async def require_premium(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TelegramUser:
    """
    Dependency that requires user to have connected channel (premium).
    Used for endpoints that modify library: add tracks, create playlists, like, follow, etc.
    """
    if not await has_channel_connected(user.id, db):
        raise HTTPException(
            status_code=403,
            detail="Подключите канал для доступа к этой функции. Перейдите в бота и используйте команду /channel"
        )
    return user


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


@router.head("/status")
async def head_status():
    """HEAD endpoint for network latency checks (used by webapp NetworkMonitor)"""
    return Response(status_code=200)


@router.get("/status", response_model=UserStatusResponse)
async def get_user_status(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user status with premium features info.
    Returns whether user has connected channel and can save tracks.
    """
    has_channel = await has_channel_connected(user.id, db)
    channel_info = await get_user_channel_info(user.id, db) if has_channel else None
    
    return UserStatusResponse(
        user=user,
        has_channel=has_channel,
        can_save=has_channel,  # Can save = has channel
        channel_info=channel_info,
    )


@router.post("/channel/verify", response_model=UserStatusResponse)
async def verify_channel_status(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Actively verify bot's access to user's configured channel via Telegram Bot API.
    Updates UserChannel.is_active if access has changed, and reconciles unavailable tracks if restored.
    """
    channel = await db.scalar(
        select(UserChannel).where(UserChannel.user_id == user.id)
    )
    if not channel:
        return UserStatusResponse(
            user=user,
            has_channel=False,
            can_save=False,
            channel_info=None,
            error="Канал не настроен. Подключите канал через команду /channel в боте.",
        )

    from bot.services.channels import get_channel_service
    ch_svc = get_channel_service()

    error_msg = None
    if ch_svc and ch_svc.bot:
        success, title, err = await ch_svc.verify_channel_access(channel.channel_id)
        if success:
            if not channel.is_active:
                channel.is_active = True
                channel.updated_at = utcnow()
            if title:
                channel.channel_title = title
            await db.commit()
            # Reconcile tracks if access restored
            await ch_svc.reconcile_channel_tracks(user.id)
        else:
            error_msg = err or "Бот не имеет прав администратора в канале"
            if channel.is_active:
                channel.is_active = False
                channel.updated_at = utcnow()
                await db.commit()
    else:
        error_msg = "Сервис бота недоступен для проверки"

    has_channel = channel.is_active
    channel_info = {
        "channel_id": channel.channel_id,
        "channel_username": channel.channel_username,
        "channel_title": channel.channel_title,
        "auto_forward": channel.auto_forward,
    } if has_channel else None

    return UserStatusResponse(
        user=user,
        has_channel=has_channel,
        can_save=has_channel,
        channel_info=channel_info,
        error=error_msg,
    )


@router.post("/generate-code", response_model=CodeGenerated)
async def generate_code_for_user(
    user_id: int,
    first_name: str,
    last_name: Optional[str] = None,
    username: Optional[str] = None,
    x_bot_secret: str = Header(..., alias="X-Bot-Secret"),
):
    """
    Generate auth code for user (called by bot).
    Bot must provide secret key for security.
    """
    # Verify bot secret
    if x_bot_secret != settings.secret_key:
        raise HTTPException(status_code=403, detail="Invalid bot secret")
    
    # Cleanup expired codes
    cleanup_expired_codes()
    
    # Remove any existing codes for this user
    existing = [code for code, data in auth_codes.items() if data["user_id"] == user_id]
    for code in existing:
        del auth_codes[code]
    
    # Generate new code
    code = generate_auth_code()
    expires_in = 300  # 5 minutes
    
    auth_codes[code] = {
        "user_id": user_id,
        "user_data": {
            "id": user_id,
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
        },
        "expires": datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    }
    
    return CodeGenerated(code=code, expires_in=expires_in)


@router.post("/verify-code", response_model=AuthResult)
async def verify_auth_code(data: CodeVerify):
    """
    Verify auth code and return JWT token.
    Used for browser authentication.
    """
    # Cleanup expired codes
    cleanup_expired_codes()
    
    code = data.code.strip()
    
    if code not in auth_codes:
        raise HTTPException(status_code=401, detail="Неверный или истёкший код")
    
    code_data = auth_codes[code]
    
    # Check expiration
    if datetime.now(timezone.utc) > code_data["expires"]:
        del auth_codes[code]
        raise HTTPException(status_code=401, detail="Код истёк")
    
    # Create user object
    user_data = code_data["user_data"]
    user = TelegramUser(
        id=user_data["id"],
        first_name=user_data["first_name"],
        last_name=user_data.get("last_name"),
        username=user_data.get("username"),
    )
    
    # Ensure user in database
    await ensure_user_in_db(user)
    
    # Create JWT token
    token = create_jwt_token(user)
    
    # Remove used code
    del auth_codes[code]
    
    return AuthResult(valid=True, user=user, token=token)


@router.get("/config")
async def get_auth_config():
    """
    Get authentication configuration for frontend.
    """
    return {
        "bot_username": settings.bot_username,
        "auth_method": "code",  # Changed from widget to code
    }


@router.post("/refresh", response_model=AuthResult)
async def refresh_token(user: TelegramUser = Depends(get_current_user)):
    """Refresh JWT token"""
    token = create_jwt_token(user)
    return AuthResult(valid=True, user=user, token=token)


# ============== Privacy Settings ==============

class PrivacySettingsRequest(BaseModel):
    hide_from_search: Optional[bool] = None
    hide_profile: Optional[bool] = None
    hide_telegram_id: Optional[bool] = None
    notify_subscription: Optional[bool] = None


class PrivacySettingsResponse(BaseModel):
    hide_from_search: bool
    hide_profile: bool
    hide_telegram_id: bool
    notify_subscription: bool


@router.get("/privacy", response_model=PrivacySettingsResponse)
async def get_privacy_settings(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's privacy settings"""
    db_user = await db.get(User, user.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return PrivacySettingsResponse(
        hide_from_search=db_user.hide_from_search or False,
        hide_profile=db_user.hide_profile or False,
        hide_telegram_id=db_user.hide_telegram_id or False,
        notify_subscription=db_user.notify_subscription if db_user.notify_subscription is not None else True,
    )


@router.put("/privacy", response_model=PrivacySettingsResponse)
async def update_privacy_settings(
    settings_data: PrivacySettingsRequest,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user's privacy settings"""
    db_user = await db.get(User, user.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if settings_data.hide_from_search is not None:
        db_user.hide_from_search = settings_data.hide_from_search
    
    if settings_data.hide_profile is not None:
        db_user.hide_profile = settings_data.hide_profile

    if settings_data.hide_telegram_id is not None:
        db_user.hide_telegram_id = settings_data.hide_telegram_id
    
    if settings_data.notify_subscription is not None:
        db_user.notify_subscription = settings_data.notify_subscription
    
    await db.commit()
    await db.refresh(db_user)
    
    return PrivacySettingsResponse(
        hide_from_search=db_user.hide_from_search or False,
        hide_profile=db_user.hide_profile or False,
        hide_telegram_id=db_user.hide_telegram_id or False,
        notify_subscription=db_user.notify_subscription if db_user.notify_subscription is not None else True,
    )


# ============== Profile Customization ==============

class ProfileUpdateRequest(BaseModel):
    custom_nickname: Optional[str] = None
    custom_avatar_url: Optional[str] = None
    clear_avatar: Optional[bool] = False


@router.put("/profile", response_model=TelegramUser)
async def update_profile(
    profile_data: ProfileUpdateRequest,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user profile nickname or avatar URL"""
    db_user = await db.get(User, user.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if profile_data.custom_nickname is not None:
        val = profile_data.custom_nickname.strip()
        db_user.custom_nickname = val if val else None

    if profile_data.clear_avatar:
        if db_user.custom_avatar_url and db_user.custom_avatar_url.startswith("/api/avatars/"):
            old_file = AVATARS_DIR / db_user.custom_avatar_url.replace("/api/avatars/", "")
            if old_file.exists() and old_file.is_file():
                try:
                    old_file.unlink()
                except OSError:
                    pass
        db_user.custom_avatar_url = None
    elif profile_data.custom_avatar_url is not None:
        db_user.custom_avatar_url = profile_data.custom_avatar_url.strip() or None

    await db.commit()
    await db.refresh(db_user)

    user.custom_nickname = db_user.custom_nickname
    user.custom_avatar_url = db_user.custom_avatar_url
    user.hide_telegram_id = db_user.hide_telegram_id or False
    return user


@router.post("/profile/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload custom avatar image"""
    db_user = await db.get(User, user.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    content_type = file.content_type or ""
    if not (content_type.startswith("image/") or content_type in ["application/octet-stream"]):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image size exceeds 10MB limit")

    ext = "jpg"
    if file.filename and "." in file.filename:
        ext = file.filename.rsplit(".", 1)[1].lower()
        if ext not in ["jpg", "jpeg", "png", "webp", "gif"]:
            ext = "jpg"

    # Remove old avatar file if local
    if db_user.custom_avatar_url and db_user.custom_avatar_url.startswith("/api/avatars/"):
        old_file = AVATARS_DIR / db_user.custom_avatar_url.replace("/api/avatars/", "")
        if old_file.exists() and old_file.is_file():
            try:
                old_file.unlink()
            except OSError:
                pass

    avatar_url = None

    # Upload directly to user's Telegram channel or PM (same as playlist covers)
    if settings.bot_token and settings.bot_token != "dummy":
        user_channel = await db.scalar(
            select(UserChannel).where(UserChannel.user_id == user.id, UserChannel.is_active == True)
        )
        target_chat_id = user_channel.channel_id if user_channel else user.id
        caption = f"👤 <b>Аватар профиля</b>: {db_user.display_name}\n\n#profile #avatar"

        try:
            from api.routers.images import _get_bot
            bot = _get_bot()
            sent_msg = None
            try:
                sent_msg = await bot.send_photo(
                    chat_id=target_chat_id,
                    photo=BufferedInputFile(file=content, filename=file.filename or f"avatar.{ext}"),
                    caption=caption,
                )
            except Exception as e:
                logger.warning(f"Failed to upload avatar to target channel {target_chat_id}: {e}")
                if user_channel and target_chat_id != user.id:
                    sent_msg = await bot.send_photo(
                        chat_id=user.id,
                        photo=BufferedInputFile(file=content, filename=file.filename or f"avatar.{ext}"),
                        caption=caption,
                    )
                else:
                    raise

            photos = sent_msg.photo or [] if sent_msg else []
            if photos:
                file_id = photos[-1].file_id
                avatar_url = f"/api/images/{file_id}"
        except Exception as e:
            logger.warning(f"Failed to upload avatar to Telegram: {e}. Falling back to local storage.")

    # Fallback to local storage if Telegram upload was not available or failed
    if not avatar_url:
        filename = f"avatar_{user.id}_{int(datetime.now(timezone.utc).timestamp())}.{ext}"
        filepath = AVATARS_DIR / filename
        with open(filepath, "wb") as f:
            f.write(content)
        avatar_url = f"/api/avatars/{filename}"

    db_user.custom_avatar_url = avatar_url
    await db.commit()
    await db.refresh(db_user)

    user.custom_avatar_url = avatar_url
    user.custom_nickname = db_user.custom_nickname
    user.hide_telegram_id = db_user.hide_telegram_id or False
    return {
        "status": "ok",
        "avatar_url": avatar_url,
        "user": user,
    }


@router.delete("/profile/avatar", response_model=TelegramUser)
async def delete_avatar(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete custom avatar"""
    db_user = await db.get(User, user.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if db_user.custom_avatar_url and db_user.custom_avatar_url.startswith("/api/avatars/"):
        old_file = AVATARS_DIR / db_user.custom_avatar_url.replace("/api/avatars/", "")
        if old_file.exists() and old_file.is_file():
            try:
                old_file.unlink()
            except OSError:
                pass

    db_user.custom_avatar_url = None
    await db.commit()
    await db.refresh(db_user)

    user.custom_avatar_url = None
    user.custom_nickname = db_user.custom_nickname
    user.hide_telegram_id = db_user.hide_telegram_id or False
    return user

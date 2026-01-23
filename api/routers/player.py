"""
TG Player API - Player Router
Handles audio streaming with secure proxy (token never exposed to browser)
"""
from typing import Optional
import time
import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import aiohttp

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.config import get_settings
from shared.database import get_db
from shared.models import Track

from .auth import get_current_user, TelegramUser


router = APIRouter()
settings = get_settings()

# Cache for Telegram file paths (not full URLs!)
_file_path_cache: dict[str, tuple[str, float]] = {}
FILE_PATH_CACHE_TTL = 3000  # 50 minutes

# Secure token cache: maps temporary token -> (track_id, user_id, expires)
_stream_tokens: dict[str, tuple[int, int, float]] = {}
STREAM_TOKEN_TTL = 300  # 5 minutes for token validity


class StreamUrlResponse(BaseModel):
    url: str  # Now returns proxy URL, not Telegram URL
    expires_at: int
    track_id: int


def generate_stream_token(track_id: int, user_id: int) -> str:
    """Generate a secure temporary token for streaming"""
    token = secrets.token_urlsafe(32)
    expires = time.time() + STREAM_TOKEN_TTL
    _stream_tokens[token] = (track_id, user_id, expires)
    
    # Cleanup old tokens
    now = time.time()
    expired = [k for k, v in _stream_tokens.items() if v[2] < now]
    for k in expired:
        del _stream_tokens[k]
    
    return token


def validate_stream_token(token: str) -> Optional[tuple[int, int]]:
    """Validate token and return (track_id, user_id) or None"""
    if token not in _stream_tokens:
        return None
    
    track_id, user_id, expires = _stream_tokens[token]
    if time.time() > expires:
        del _stream_tokens[token]
        return None
    
    return (track_id, user_id)


async def get_telegram_file_path(file_id: str) -> Optional[str]:
    """
    Get file path from Telegram (not full URL).
    """
    import logging
    logger = logging.getLogger("uvicorn.error")
    
    # Check cache
    if file_id in _file_path_cache:
        file_path, expires = _file_path_cache[file_id]
        if time.time() < expires:
            logger.debug(f"File path cache hit for {file_id[:20]}...")
            return file_path
    
    # Call Telegram API
    api_url = f"https://api.telegram.org/bot{settings.bot_token}/getFile"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, params={"file_id": file_id}) as resp:
            if resp.status != 200:
                logger.error(f"Telegram getFile failed: status={resp.status}, file_id={file_id[:20]}...")
                return None
            
            data = await resp.json()
            
            if not data.get("ok"):
                error_desc = data.get("description", "Unknown error")
                logger.error(f"Telegram getFile error: {error_desc}, file_id={file_id[:20]}...")
                return None
            
            file_path = data.get("result", {}).get("file_path")
            if not file_path:
                logger.error(f"No file_path in response for file_id={file_id[:20]}...")
                return None
            
            # Cache the file path
            _file_path_cache[file_id] = (file_path, time.time() + FILE_PATH_CACHE_TTL)
            logger.info(f"Got file path: {file_path}")
            
            return file_path


@router.get("/stream/{track_id}", response_model=StreamUrlResponse)
async def get_stream_url(
    track_id: int,
    request: Request,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get secure proxy URL for streaming a track.
    Returns a temporary token-based URL that proxies through our server.
    Bot token is NEVER exposed to the client.
    """
    # Get track
    track = await db.scalar(
        select(Track).where(
            Track.id == track_id,
            Track.user_id == user.id
        )
    )
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Verify file is accessible (pre-cache the path)
    file_path = await get_telegram_file_path(track.file_id)
    
    if not file_path:
        raise HTTPException(
            status_code=503,
            detail="Could not get file from Telegram. File might be too large (>20MB) or unavailable."
        )
    
    # Generate secure temporary token
    token = generate_stream_token(track_id, user.id)
    
    # Build proxy URL (relative to current host)
    base_url = str(request.base_url).rstrip('/')
    proxy_url = f"{base_url}/api/player/audio/{token}"
    
    expires_at = int(time.time()) + STREAM_TOKEN_TTL
    
    return StreamUrlResponse(
        url=proxy_url,
        expires_at=expires_at,
        track_id=track_id,
    )


@router.get("/audio/{token}")
async def stream_audio(token: str, db: AsyncSession = Depends(get_db)):
    """
    Secure audio proxy endpoint.
    Streams audio through our server - bot token never exposed to client.
    """
    # Validate token
    token_data = validate_stream_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired stream token")
    
    track_id, user_id = token_data
    
    # Get track
    track = await db.scalar(
        select(Track).where(
            Track.id == track_id,
            Track.user_id == user_id
        )
    )
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Get file path from Telegram
    file_path = await get_telegram_file_path(track.file_id)
    if not file_path:
        raise HTTPException(status_code=503, detail="File unavailable")
    
    # Stream from Telegram through our proxy
    telegram_url = f"https://api.telegram.org/file/bot{settings.bot_token}/{file_path}"
    
    async def stream_generator():
        async with aiohttp.ClientSession() as session:
            async with session.get(telegram_url) as resp:
                async for chunk in resp.content.iter_chunked(64 * 1024):  # 64KB chunks
                    yield chunk
    
    # Determine content type
    content_type = track.mime_type or "audio/mpeg"
    
    # Sanitize filename for Content-Disposition header (ASCII only)
    import re
    safe_title = re.sub(r'[^\w\s.-]', '', track.title or 'audio')
    safe_title = safe_title.encode('ascii', 'ignore').decode('ascii') or 'audio'
    
    return StreamingResponse(
        stream_generator(),
        media_type=content_type,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Disposition": f'inline; filename="{safe_title}.mp3"',
            "Cache-Control": "private, max-age=300",  # Cache 5 min on client
        }
    )


@router.post("/stream/batch")
async def get_batch_stream_urls(
    track_ids: list[int],
    request: Request,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get secure proxy URLs for multiple tracks at once.
    """
    if len(track_ids) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 tracks per request")
    
    # Get tracks
    result = await db.execute(
        select(Track).where(
            Track.id.in_(track_ids),
            Track.user_id == user.id
        )
    )
    tracks = {t.id: t for t in result.scalars().all()}
    
    base_url = str(request.base_url).rstrip('/')
    urls = []
    expires_at = int(time.time()) + STREAM_TOKEN_TTL
    
    for track_id in track_ids:
        track = tracks.get(track_id)
        if not track:
            urls.append({
                "track_id": track_id,
                "url": None,
                "error": "Track not found"
            })
            continue
        
        token = generate_stream_token(track_id, user.id)
        urls.append({
            "track_id": track_id,
            "url": f"{base_url}/api/player/audio/{token}",
            "expires_at": expires_at,
            "error": None
        })
    
    return {"urls": urls}


@router.post("/play/{track_id}")
async def record_play(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Record that a track was fully played.
    Increments play_count for statistics.
    """
    # Get track
    track = await db.scalar(
        select(Track).where(
            Track.id == track_id,
            Track.user_id == user.id
        )
    )
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Increment play count
    track.play_count = (track.play_count or 0) + 1
    track.last_played_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "success": True,
        "track_id": track_id,
        "play_count": track.play_count
    }

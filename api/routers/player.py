"""
TG Player API - Player Router
Handles audio streaming URLs
"""
from typing import Optional
import time
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
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

# Simple in-memory cache for file URLs (production: use Redis)
_url_cache: dict[str, tuple[str, float]] = {}
URL_CACHE_TTL = 3000  # 50 minutes (Telegram URLs valid for ~1 hour)


class StreamUrlResponse(BaseModel):
    url: str
    expires_at: int  # Unix timestamp
    track_id: int


async def get_telegram_file_url(file_id: str) -> Optional[str]:
    """
    Get download URL for Telegram file.
    Uses Bot API getFile method.
    """
    # Check cache first
    if file_id in _url_cache:
        url, expires = _url_cache[file_id]
        if time.time() < expires:
            return url
    
    # Call Telegram API
    api_url = f"https://api.telegram.org/bot{settings.bot_token}/getFile"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, params={"file_id": file_id}) as resp:
            if resp.status != 200:
                return None
            
            data = await resp.json()
            
            if not data.get("ok"):
                return None
            
            file_path = data.get("result", {}).get("file_path")
            if not file_path:
                return None
            
            # Construct download URL
            download_url = f"https://api.telegram.org/file/bot{settings.bot_token}/{file_path}"
            
            # Cache the URL
            _url_cache[file_id] = (download_url, time.time() + URL_CACHE_TTL)
            
            return download_url


@router.get("/stream/{track_id}", response_model=StreamUrlResponse)
async def get_stream_url(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get streaming URL for a track.
    Returns a temporary URL that can be used directly in <audio> element.
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
    
    # Get Telegram file URL
    url = await get_telegram_file_url(track.file_id)
    
    if not url:
        raise HTTPException(
            status_code=503,
            detail="Could not get file URL from Telegram. File might be too large (>20MB) or unavailable."
        )
    
    # Calculate expiration (50 minutes from now to be safe)
    expires_at = int(time.time()) + URL_CACHE_TTL
    
    return StreamUrlResponse(
        url=url,
        expires_at=expires_at,
        track_id=track_id,
    )


@router.post("/stream/batch")
async def get_batch_stream_urls(
    track_ids: list[int],
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get streaming URLs for multiple tracks at once.
    Useful for preloading playlist.
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
    
    # Get URLs
    urls = []
    expires_at = int(time.time()) + URL_CACHE_TTL
    
    for track_id in track_ids:
        track = tracks.get(track_id)
        if not track:
            urls.append({
                "track_id": track_id,
                "url": None,
                "error": "Track not found"
            })
            continue
        
        url = await get_telegram_file_url(track.file_id)
        urls.append({
            "track_id": track_id,
            "url": url,
            "expires_at": expires_at if url else None,
            "error": None if url else "Could not get URL"
        })
    
    return {"urls": urls}

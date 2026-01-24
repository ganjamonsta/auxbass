"""
TG Player API - Player Router
Handles audio streaming with secure proxy (token never exposed to browser)
"""
from typing import Optional
import logging
import re
import time
import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Header, Response
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
from shared.models import Track, UserLibrary

from .auth import get_current_user, TelegramUser


logger = logging.getLogger("uvicorn.error")

router = APIRouter()
settings = get_settings()

# ============== Global HTTP Session Pool ==============
# Reuses TCP connections instead of creating new ones per request
# This saves ~100-200ms per request on TLS handshake
_http_session: Optional[aiohttp.ClientSession] = None


async def get_http_session() -> aiohttp.ClientSession:
    """Get or create global aiohttp session with connection pooling"""
    global _http_session
    if _http_session is None or _http_session.closed:
        # Connection pool: keep up to 100 connections, 10 per host
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=10,
            ttl_dns_cache=300,  # Cache DNS for 5 minutes
            keepalive_timeout=60,  # Keep connections alive for 60s
        )
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        _http_session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
        )
    return _http_session


async def close_http_session():
    """Close global HTTP session (call on app shutdown)"""
    global _http_session
    if _http_session and not _http_session.closed:
        await _http_session.close()
        _http_session = None


# Cache for Telegram file paths (not full URLs!)
_file_path_cache: dict[str, tuple[str, float]] = {}
FILE_PATH_CACHE_TTL = 3000  # 50 minutes

# Secure token cache: maps temporary token -> (track_id, user_id, file_path, expires)
# file_path is cached to avoid second Telegram API call when streaming
_stream_tokens: dict[str, tuple[int, int, str, float]] = {}
STREAM_TOKEN_TTL = 300  # 5 minutes for token validity


class StreamUrlResponse(BaseModel):
    url: str  # Now returns proxy URL, not Telegram URL
    expires_at: int
    track_id: int


def generate_stream_token(track_id: int, user_id: int, file_path: str) -> str:
    """Generate a secure temporary token for streaming with cached file_path"""
    token = secrets.token_urlsafe(32)
    expires = time.time() + STREAM_TOKEN_TTL
    _stream_tokens[token] = (track_id, user_id, file_path, expires)
    
    # Cleanup old tokens (limit cleanup to avoid O(n) on every call)
    now = time.time()
    if len(_stream_tokens) > 1000:
        expired = [k for k, v in _stream_tokens.items() if v[3] < now]
        for k in expired:
            del _stream_tokens[k]
    
    return token


def validate_stream_token(token: str) -> Optional[tuple[int, int, str]]:
    """Validate token and return (track_id, user_id, file_path) or None"""
    if token not in _stream_tokens:
        return None
    
    track_id, user_id, file_path, expires = _stream_tokens[token]
    if time.time() > expires:
        del _stream_tokens[token]
        return None
    
    return (track_id, user_id, file_path)


async def get_telegram_file_path(file_id: str) -> Optional[str]:
    """
    Get file path from Telegram (not full URL).
    Uses global session pool for better performance.
    """
    # Check cache
    if file_id in _file_path_cache:
        file_path, expires = _file_path_cache[file_id]
        if time.time() < expires:
            logger.debug(f"File path cache hit for {file_id[:20]}...")
            return file_path
    
    # Call Telegram API using pooled session
    # Use configurable API URL (supports local Telegram Bot API server for >20MB files)
    base_url = settings.telegram_api_url.rstrip('/')
    api_url = f"{base_url}/bot{settings.bot_token}/getFile"
    
    session = await get_http_session()
    try:
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
    except aiohttp.ClientError as e:
        logger.error(f"HTTP error getting file path: {e}")
        return None


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
    
    Users can stream:
    - Any public track (from global library)
    - Their own private tracks
    """
    # Get track (any track, we'll check permissions)
    track = await db.scalar(
        select(Track).where(Track.id == track_id)
    )
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Check access: public tracks are accessible to everyone, private only to uploader
    if not track.is_public and track.user_id != user.id:
        raise HTTPException(status_code=403, detail="This track is private")
    
    # Verify file is accessible (pre-cache the path)
    file_path = await get_telegram_file_path(track.file_id)
    
    if not file_path:
        # Check if file is too large (>20MB limit for standard Bot API)
        file_size_mb = (track.file_size or 0) / (1024 * 1024)
        if file_size_mb > 20:
            raise HTTPException(
                status_code=503,
                detail=f"Файл слишком большой ({file_size_mb:.1f} MB). Telegram Bot API поддерживает скачивание только файлов до 20 MB. Используйте кнопку 'Скачать' в боте."
            )
        raise HTTPException(
            status_code=503,
            detail="Не удалось получить файл от Telegram. Файл возможно удалён или недоступен."
        )
    
    # Generate secure temporary token with cached file_path
    token = generate_stream_token(track_id, user.id, file_path)
    
    # Return relative URL to avoid Mixed Content issues (HTTP vs HTTPS)
    # The frontend will resolve this against its own origin
    proxy_url = f"/api/player/audio/{token}"
    
    expires_at = int(time.time()) + STREAM_TOKEN_TTL
    
    return StreamUrlResponse(
        url=proxy_url,
        expires_at=expires_at,
        track_id=track_id,
    )


@router.get("/audio/{token}")
async def stream_audio(
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    range: Optional[str] = Header(None),
):
    """
    Secure audio proxy endpoint with Range request support.
    Streams audio through our server - bot token never exposed to client.
    Supports HTTP 206 Partial Content for fast seeking.
    """
    # Validate token - now includes cached file_path (saves ~300ms Telegram API call)
    token_data = validate_stream_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired stream token")
    
    track_id, user_id, file_path = token_data
    
    # Get track for metadata (file_path already validated and cached in token)
    # Note: user_id in token is just for logging, access was validated when token was created
    track = await db.scalar(
        select(Track).where(Track.id == track_id)
    )
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # file_path is already in token - no need for second Telegram API call!
    if not file_path:
        raise HTTPException(status_code=503, detail="File unavailable")
    
    # Stream from Telegram through our proxy
    # Use configurable API URL (supports local Telegram Bot API server for >20MB files)
    base_url = settings.telegram_api_url.rstrip('/')
    telegram_url = f"{base_url}/file/bot{settings.bot_token}/{file_path}"
    
    # Determine content type and filename
    content_type = track.mime_type or "audio/mpeg"
    safe_title = re.sub(r'[^\w\s.-]', '', track.title or 'audio')
    safe_title = safe_title.encode('ascii', 'ignore').decode('ascii') or 'audio'
    
    # Get file size from track or fetch from Telegram
    file_size = track.file_size
    
    # Parse Range header
    start_byte = 0
    end_byte = None
    
    if range and range.startswith("bytes="):
        try:
            range_spec = range[6:]  # Remove "bytes="
            if range_spec.startswith("-"):
                # Last N bytes: bytes=-500
                if file_size:
                    start_byte = max(0, file_size - int(range_spec[1:]))
            elif "-" in range_spec:
                parts = range_spec.split("-")
                start_byte = int(parts[0]) if parts[0] else 0
                if parts[1]:
                    end_byte = int(parts[1])
        except (ValueError, IndexError):
            pass
    
    # Build headers for Telegram request
    telegram_headers = {}
    if start_byte > 0 or end_byte:
        range_value = f"bytes={start_byte}-"
        if end_byte:
            range_value = f"bytes={start_byte}-{end_byte}"
        telegram_headers["Range"] = range_value
    
    # Make request to Telegram FIRST to validate and get actual content info
    session = await get_http_session()
    try:
        telegram_response = await session.get(telegram_url, headers=telegram_headers)
    except aiohttp.ClientError as e:
        logger.error(f"Failed to connect to Telegram for streaming: {e}")
        raise HTTPException(status_code=503, detail="Failed to fetch audio from Telegram")
    
    # Check if Telegram returned an error
    if telegram_response.status >= 400:
        await telegram_response.release()
        logger.error(f"Telegram returned error {telegram_response.status} for file {file_path}")
        if telegram_response.status == 404:
            raise HTTPException(status_code=404, detail="File no longer available on Telegram")
        raise HTTPException(status_code=503, detail=f"Telegram error: {telegram_response.status}")
    
    # Get ACTUAL content length from Telegram response (not from our DB!)
    actual_content_length = telegram_response.headers.get("Content-Length")
    telegram_content_range = telegram_response.headers.get("Content-Range")
    
    async def stream_generator():
        """Stream audio from already-opened Telegram response"""
        try:
            async for chunk in telegram_response.content.iter_chunked(64 * 1024):
                yield chunk
        finally:
            await telegram_response.release()
    
    # Build response headers
    response_headers = {
        "Accept-Ranges": "bytes",
        "Content-Disposition": f'inline; filename="{safe_title}.mp3"',
        "Cache-Control": "private, max-age=3600",  # Cache 1 hour
    }
    
    # If Telegram returned 206 Partial Content, pass it through
    if telegram_response.status == 206 and telegram_content_range:
        response_headers["Content-Range"] = telegram_content_range
        if actual_content_length:
            response_headers["Content-Length"] = actual_content_length
        
        return StreamingResponse(
            stream_generator(),
            status_code=206,
            media_type=content_type,
            headers=response_headers,
        )
    
    # Regular 200 response - use actual content length from Telegram
    if actual_content_length:
        response_headers["Content-Length"] = actual_content_length
    
    return StreamingResponse(
        stream_generator(),
        media_type=content_type,
        headers=response_headers,
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
    Pre-fetches Telegram file paths in parallel for faster playback.
    """
    import asyncio
    
    if len(track_ids) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 tracks per request")
    
    # Get tracks (allow public tracks from any user)
    from sqlalchemy import or_
    result = await db.execute(
        select(Track).where(
            Track.id.in_(track_ids),
            or_(
                Track.is_public == True,
                Track.user_id == user.id
            )
        )
    )
    tracks = {t.id: t for t in result.scalars().all()}
    
    # Pre-fetch all file paths in parallel (key optimization!)
    async def get_file_path_for_track(track):
        try:
            return await get_telegram_file_path(track.file_id)
        except Exception as e:
            logger.debug(f"Failed to get file path for track {track.id}: {e}")
            return None
    
    # Fetch all file paths concurrently
    file_path_tasks = []
    track_order = []
    for track_id in track_ids:
        track = tracks.get(track_id)
        if track:
            file_path_tasks.append(get_file_path_for_track(track))
            track_order.append(track_id)
    
    file_paths = await asyncio.gather(*file_path_tasks, return_exceptions=True)
    file_path_map = dict(zip(track_order, file_paths))
    
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
        
        file_path = file_path_map.get(track_id)
        if isinstance(file_path, Exception) or not file_path:
            urls.append({
                "track_id": track_id,
                "url": None,
                "error": "Could not get file path"
            })
            continue
        
        # Generate token WITH cached file_path (saves ~300ms on stream start)
        token = generate_stream_token(track_id, user.id, file_path)
        urls.append({
            "track_id": track_id,
            "url": f"/api/player/audio/{token}",  # Relative URL
            "expires_at": expires_at,
            "error": None
        })
    
    return {"urls": urls}


@router.post("/prefetch")
async def prefetch_file_paths(
    track_ids: list[int],
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Pre-cache Telegram file paths for a list of tracks.
    Call this when loading track list to speed up first play.
    Runs in background - returns immediately.
    """
    if len(track_ids) > 20:
        track_ids = track_ids[:20]  # Limit to 20 tracks
    
    # Get tracks (allow public tracks from any user)
    from sqlalchemy import or_
    result = await db.execute(
        select(Track).where(
            Track.id.in_(track_ids),
            or_(
                Track.is_public == True,
                Track.user_id == user.id
            )
        )
    )
    tracks = result.scalars().all()
    
    # Prefetch file paths in parallel (fire and forget style, but we await for better caching)
    import asyncio
    
    async def prefetch_one(track):
        try:
            await get_telegram_file_path(track.file_id)
        except Exception as e:
            logger.debug(f"Prefetch failed for track {track.id}: {e}")
    
    # Run all prefetches concurrently
    await asyncio.gather(*[prefetch_one(t) for t in tracks], return_exceptions=True)
    
    return {
        "success": True,
        "prefetched": len(tracks),
        "message": f"Prefetched {len(tracks)} file paths"
    }


@router.post("/play/{track_id}")
async def record_play(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Record that a track was fully played.
    Increments global play_count and user's personal play_count.
    """
    # Get track (any public track or own)
    track = await db.scalar(
        select(Track).where(Track.id == track_id)
    )
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    if not track.is_public and track.user_id != user.id:
        raise HTTPException(status_code=403, detail="Track is private")
    
    # Increment global play count
    track.play_count = (track.play_count or 0) + 1
    track.last_played_at = datetime.utcnow()
    
    # Update user's library entry if exists
    lib_entry = await db.scalar(
        select(UserLibrary).where(
            UserLibrary.user_id == user.id,
            UserLibrary.track_id == track_id
        )
    )
    
    if lib_entry:
        lib_entry.play_count = (lib_entry.play_count or 0) + 1
        lib_entry.last_played_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "success": True,
        "track_id": track_id,
        "play_count": track.play_count,
        "user_play_count": lib_entry.play_count if lib_entry else 0
    }


@router.post("/download/{track_id}")
async def download_track(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send track to user via Telegram bot (download).
    Uses sendAudio to forward the file from bot to user.
    Works for any public track.
    """
    # Get track (any public track or own)
    track = await db.scalar(
        select(Track).where(Track.id == track_id)
    )
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    if not track.is_public and track.user_id != user.id:
        raise HTTPException(status_code=403, detail="Track is private")
    
    # Send audio via Bot API (sendAudio works for any file size, unlike getFile)
    base_url = settings.telegram_api_url.rstrip('/')
    api_url = f"{base_url}/bot{settings.bot_token}/sendAudio"
    
    caption = f"🎧 {track.artist or 'Неизвестен'} - {track.title or 'Без названия'}"
    
    payload = {
        "chat_id": user.id,
        "audio": track.file_id,
        "caption": caption,
        "performer": track.artist,
        "title": track.title,
    }
    if track.duration:
        payload["duration"] = track.duration
    
    session = await get_http_session()
    try:
        async with session.post(api_url, json=payload) as resp:
            data = await resp.json()
            
            if not data.get("ok"):
                error_desc = data.get("description", "Unknown error")
                logger.error(f"Telegram sendAudio error: {error_desc}")
                raise HTTPException(status_code=503, detail=f"Failed to send: {error_desc}")
            
            return {"success": True, "track_id": track_id}
    except aiohttp.ClientError as e:
        logger.error(f"HTTP error sending audio: {e}")
        raise HTTPException(status_code=503, detail="Failed to send audio")


class DownloadPlaylistRequest(BaseModel):
    track_ids: list[int]
    playlist_name: str = "Плейлист"


@router.post("/download-playlist")
async def download_playlist(
    request: DownloadPlaylistRequest,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send multiple tracks as media group via Telegram bot.
    Tracks are sent in batches of 10 (Telegram limit).
    Header message is sent first, then audio batches.
    """
    if not request.track_ids:
        raise HTTPException(status_code=400, detail="No tracks provided")
    
    # Get tracks
    result = await db.execute(
        select(Track).where(
            Track.id.in_(request.track_ids),
            Track.user_id == user.id
        )
    )
    tracks_map = {t.id: t for t in result.scalars().all()}
    
    # Maintain order from request
    tracks = [tracks_map[tid] for tid in request.track_ids if tid in tracks_map]
    
    if not tracks:
        raise HTTPException(status_code=404, detail="No tracks found")
    
    session = await get_http_session()
    
    # Send header message first
    total_batches = (len(tracks) + 9) // 10
    header_text = f"📁 <b>Плейлист: {request.playlist_name}</b>\n🎵 {len(tracks)} треков"
    if total_batches > 1:
        header_text += f"\n📦 Будет отправлено {total_batches} сообщениями"
    
    header_url = f"https://api.telegram.org/bot{settings.bot_token}/sendMessage"
    header_payload = {
        "chat_id": user.id,
        "text": header_text,
        "parse_mode": "HTML"
    }
    
    try:
        async with session.post(header_url, json=header_payload) as resp:
            pass  # Header sent
    except:
        pass  # Continue even if header fails
    
    api_url = f"https://api.telegram.org/bot{settings.bot_token}/sendMediaGroup"
    
    batch_size = 10
    total_sent = 0
    
    for i in range(0, len(tracks), batch_size):
        batch = tracks[i:i + batch_size]
        
        # Build media group (no captions - header already sent)
        media = []
        for track in batch:
            item = {
                "type": "audio",
                "media": track.file_id,
                "performer": track.artist or "",
                "title": track.title or "Без названия",
            }
            if track.duration:
                item["duration"] = track.duration
            media.append(item)
        
        payload = {
            "chat_id": user.id,
            "media": media,
        }
        
        try:
            async with session.post(api_url, json=payload) as resp:
                data = await resp.json()
                
                if data.get("ok"):
                    total_sent += len(batch)
                else:
                    # If media group fails, try sending individually
                    for track in batch:
                        try:
                            single_url = f"https://api.telegram.org/bot{settings.bot_token}/sendAudio"
                            single_payload = {
                                "chat_id": user.id,
                                "audio": track.file_id,
                                "performer": track.artist,
                                "title": track.title,
                            }
                            async with session.post(single_url, json=single_payload) as single_resp:
                                if (await single_resp.json()).get("ok"):
                                    total_sent += 1
                        except:
                            continue
            
            # Delay between batches to avoid flood limits
            if i + batch_size < len(tracks):
                import asyncio
                await asyncio.sleep(1.0)
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error sending media group: {e}")
    
    return {"success": True, "sent": total_sent, "total": len(tracks)}
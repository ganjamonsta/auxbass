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
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
import aiohttp
import asyncio

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.config import get_settings
from shared.database import get_db
from shared.models import Track, UserLibrary, ChannelMessage, UserChannel
from shared.matching import normalize_title, normalize_artist

from .auth import get_current_user
from .library import is_streamable, is_hd_format, STREAMABLE_MIME_TYPES, HD_MIME_TYPES
from api.schemas_v2.player import StreamUrlResponse, DownloadPlaylistRequest
from api.schemas_v2.common import TelegramUser


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
        # Timeouts:
        # - total=None: No limit on total request time (needed for large file streaming)
        # - connect=10: 10 seconds to establish connection
        # - sock_read=60: 60 seconds max between data chunks (detects stalled connections)
        timeout = aiohttp.ClientTimeout(
            total=None,       # No total limit - files can be large!
            connect=10,       # Connection timeout
            sock_read=60,     # Read timeout between chunks
        )
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
STREAM_TOKEN_TTL = 3600  # 1 hour for token validity (was 5 min - too short for long tracks/pauses)


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


async def find_streamable_alternative(track: Track, db: AsyncSession) -> Optional[Track]:
    """
    Find a streamable (MP3) alternative for an HD track.
    Matches by normalized title and artist.
    """
    if not track.title:
        return None
    
    # Normalize for matching
    norm_title = normalize_title(track.title).lower()
    norm_artist = normalize_artist(track.artist or "").lower() if track.artist else None
    
    # Find MP3 tracks with similar title/artist
    # Using func.lower() for case-insensitive search in DB
    query = (
        select(Track)
        .where(Track.id != track.id)
        .where(Track.is_unavailable == False)
        .where(
            or_(
                Track.mime_type == "audio/mpeg",
                Track.mime_type == "audio/mp3",
                Track.mime_type == None,  # Legacy tracks without mime_type are usually MP3
            )
        )
    )
    
    result = await db.execute(query)
    candidates = result.scalars().all()
    
    # Find best match
    for candidate in candidates:
        if not candidate.title:
            continue
        
        cand_norm_title = normalize_title(candidate.title).lower()
        cand_norm_artist = normalize_artist(candidate.artist or "").lower() if candidate.artist else None
        
        # Match title (must be similar)
        if norm_title != cand_norm_title:
            continue
        
        # Match artist if both have artist
        if norm_artist and cand_norm_artist:
            if norm_artist != cand_norm_artist:
                continue
        
        # Found a match - prefer smaller file (more likely to stream well)
        return candidate
    
    return None


async def find_hd_alternative(track: Track, db: AsyncSession) -> Optional[Track]:
    """
    Find an HD (FLAC/WAV) alternative for an MP3 track.
    Useful to show user that HD version is available.
    """
    if not track.title:
        return None
    
    # Normalize for matching
    norm_title = normalize_title(track.title).lower()
    norm_artist = normalize_artist(track.artist or "").lower() if track.artist else None
    
    # Find HD tracks with similar title/artist
    hd_mime_list = list(HD_MIME_TYPES)
    query = (
        select(Track)
        .where(Track.id != track.id)
        .where(Track.is_unavailable == False)
        .where(Track.mime_type.in_(hd_mime_list))
    )
    
    result = await db.execute(query)
    candidates = result.scalars().all()
    
    # Find best match
    for candidate in candidates:
        if not candidate.title:
            continue
        
        cand_norm_title = normalize_title(candidate.title).lower()
        cand_norm_artist = normalize_artist(candidate.artist or "").lower() if candidate.artist else None
        
        # Match title (must be similar)
        if norm_title != cand_norm_title:
            continue
        
        # Match artist if both have artist
        if norm_artist and cand_norm_artist:
            if norm_artist != cand_norm_artist:
                continue
        
        return candidate
    
    return None


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


async def refresh_file_id_from_channel(track_id: int, db: AsyncSession) -> Optional[str]:
    """
    Try to get fresh file_id from user's channel message.
    
    When a track's file_id becomes stale, we can retrieve the message
    from the channel where it was forwarded and extract the new file_id.
    
    Returns the new file_id if successful, None otherwise.
    """
    # Find channel message for this track
    result = await db.execute(
        select(ChannelMessage, UserChannel)
        .join(UserChannel, ChannelMessage.channel_id == UserChannel.id)
        .where(ChannelMessage.track_id == track_id)
        .where(UserChannel.is_active == True)
        .limit(1)
    )
    row = result.first()
    
    if not row:
        logger.debug(f"[Refresh FileID] No channel message found for track {track_id}")
        return None
    
    channel_msg, user_channel = row
    
    # Call Telegram API to get the message
    base_url = settings.telegram_api_url.rstrip('/')
    # Use copyMessage or forwardMessage to get fresh file_id? No, use getMessages via channel
    # Actually, Bot API doesn't have getMessages. We need to use getUpdates or getChat...
    # The only way is to forward the message to ourselves and get the file_id
    # OR use getChatMember + some trick
    
    # Actually, the cleanest way: use forwardMessage to forward to the same channel (or bot's chat)
    # and then delete it. But that's ugly.
    
    # Better approach: just call getFile on the old file_id - if it fails, we truly need user to re-upload
    # BUT we can try to get the message via Bot API's copyMessage with send_copy=False... no that doesn't exist
    
    # The Bot API way: forward message to bot's own chat (or use sendAudio with file_id)
    # Let's try a trick: use sendAudio to bot's own chat with the old file_id, 
    # if it succeeds we know file is still there
    
    # Actually simplest: Telegram doesn't provide getMessages for bots without updates
    # The ONLY reliable way is for user to re-send the file, OR use Local Bot API Server
    
    # However! We can try using the channel's message_id to COPY the message which gives us new file_id
    api_url = f"{base_url}/bot{settings.bot_token}/copyMessage"
    
    session = await get_http_session()
    try:
        # Copy message from channel to the channel itself (we'll delete it after)
        async with session.post(api_url, json={
            "chat_id": user_channel.channel_id,
            "from_chat_id": user_channel.channel_id,
            "message_id": channel_msg.message_id,
        }) as resp:
            if resp.status != 200:
                logger.warning(f"[Refresh FileID] copyMessage failed: status={resp.status}")
                return None
            
            data = await resp.json()
            if not data.get("ok"):
                logger.warning(f"[Refresh FileID] copyMessage error: {data.get('description')}")
                return None
            
            new_message_id = data.get("result", {}).get("message_id")
            if not new_message_id:
                return None
            
            logger.info(f"[Refresh FileID] Copied message {channel_msg.message_id} -> {new_message_id}")
    except aiohttp.ClientError as e:
        logger.error(f"[Refresh FileID] HTTP error: {e}")
        return None
    
    # Now forward THIS new message to get audio with file_id
    # Actually copyMessage doesn't return the audio... we need forwardMessage
    # Let's delete the copied message and try forwardMessage instead
    
    # Delete the copied message
    delete_url = f"{base_url}/bot{settings.bot_token}/deleteMessage"
    try:
        async with session.post(delete_url, json={
            "chat_id": user_channel.channel_id,
            "message_id": new_message_id,
        }) as resp:
            pass  # Ignore result
    except:
        pass
    
    # Try forwardMessage which DOES return the full message with audio
    forward_url = f"{base_url}/bot{settings.bot_token}/forwardMessage"
    try:
        async with session.post(forward_url, json={
            "chat_id": user_channel.channel_id,
            "from_chat_id": user_channel.channel_id, 
            "message_id": channel_msg.message_id,
        }) as resp:
            if resp.status != 200:
                logger.warning(f"[Refresh FileID] forwardMessage failed: status={resp.status}")
                return None
            
            data = await resp.json()
            if not data.get("ok"):
                logger.warning(f"[Refresh FileID] forwardMessage error: {data.get('description')}")
                return None
            
            result_msg = data.get("result", {})
            audio = result_msg.get("audio")
            
            if not audio or not audio.get("file_id"):
                logger.warning(f"[Refresh FileID] No audio in forwarded message")
                # Delete forwarded message
                try:
                    async with session.post(delete_url, json={
                        "chat_id": user_channel.channel_id,
                        "message_id": result_msg.get("message_id"),
                    }) as resp:
                        pass
                except:
                    pass
                return None
            
            new_file_id = audio["file_id"]
            new_message_id = result_msg.get("message_id")
            
            logger.info(f"[Refresh FileID] Got fresh file_id for track {track_id}")
            
            # Delete the forwarded message (cleanup)
            try:
                async with session.post(delete_url, json={
                    "chat_id": user_channel.channel_id,
                    "message_id": new_message_id,
                }) as resp:
                    pass
            except:
                pass
            
            return new_file_id
            
    except aiohttp.ClientError as e:
        logger.error(f"[Refresh FileID] HTTP error in forwardMessage: {e}")
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
    
    For HD tracks (FLAC, WAV), automatically finds MP3 alternative if available.
    Returns info about HD version so user knows high quality is available.
    
    Users can stream:
    - Any public track (from global library)
    - Their own private tracks
    """
    # Get track (any track, we'll check permissions)
    original_track = await db.scalar(
        select(Track).where(Track.id == track_id)
    )
    
    if not original_track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Check access: public tracks are accessible to everyone, private only to uploader
    if not original_track.is_public and original_track.uploader_id != user.id:
        raise HTTPException(status_code=403, detail="This track is private")
    
    # HD track handling: find MP3 alternative
    # Check both mime_type AND file size (large files are often HD even without proper mime_type)
    track = original_track
    hd_track_info = None
    
    file_size_mb = (original_track.file_size or 0) / (1024 * 1024)
    is_track_hd = not is_streamable(original_track.mime_type)
    is_track_too_large = file_size_mb > 20
    
    if is_track_hd or is_track_too_large:
        # This is an HD track or too large - try to find MP3 alternative
        reason = f"HD format ({original_track.mime_type})" if is_track_hd else f"too large ({file_size_mb:.1f} MB)"
        logger.info(f"[Stream Request] Track {track_id} is {reason}, searching for MP3 alternative...")
        
        mp3_alt = await find_streamable_alternative(original_track, db)
        
        if mp3_alt:
            # Found MP3 alternative - use it for streaming, save HD info
            logger.info(f"[Stream Request] Found MP3 alternative: track {mp3_alt.id} for HD/large track {track_id}")
            track = mp3_alt
            hd_track_info = {
                "id": original_track.id,
                "title": original_track.title,
            }
        else:
            # No MP3 alternative - can't stream
            logger.warning(f"[Stream Request] Track {track_id} ({reason}) has no MP3 alternative")
            if is_track_hd:
                raise HTTPException(
                    status_code=503,
                    detail=f"Трек в формате высокого качества ({original_track.mime_type or 'HD'}, {file_size_mb:.1f} MB) недоступен для стриминга. MP3 версия не найдена. Используйте кнопку 'Скачать' в боте для загрузки HD версии."
                )
            else:
                raise HTTPException(
                    status_code=503,
                    detail=f"Файл слишком большой ({file_size_mb:.1f} MB). MP3 версия не найдена. Используйте кнопку 'Скачать' в боте."
                )
    
    # Verify file is accessible (pre-cache the path)
    file_path = await get_telegram_file_path(track.file_id)
    
    if not file_path:
        # Check if file is too large (>20MB limit for standard Bot API)
        file_size_mb = (track.file_size or 0) / (1024 * 1024)
        if file_size_mb > 20:
            logger.warning(f"[Stream Request] Track {track.id} too large: {file_size_mb:.1f} MB")
            raise HTTPException(
                status_code=503,
                detail=f"Файл слишком большой ({file_size_mb:.1f} MB). Telegram Bot API поддерживает скачивание только файлов до 20 MB. Используйте кнопку 'Скачать' в боте."
            )
        
        # Try to refresh file_id from channel message
        logger.info(f"[Stream Request] Track {track_id} file_id stale, attempting refresh from channel...")
        new_file_id = await refresh_file_id_from_channel(track_id, db)
        
        if new_file_id:
            # Update track with new file_id
            track.file_id = new_file_id
            track.is_unavailable = False  # Clear unavailable flag
            await db.commit()
            logger.info(f"[Stream Request] Track {track_id} file_id refreshed successfully!")
            
            # Try again with new file_id
            file_path = await get_telegram_file_path(new_file_id)
        
        if not file_path:
            # Still no luck - mark as unavailable
            if not track.is_unavailable:
                track.is_unavailable = True
                await db.commit()
                logger.warning(f"[Stream Request] Track {track_id} marked as unavailable (Telegram file_id invalid)")
            else:
                logger.warning(f"[Stream Request] Track {track_id} file unavailable from Telegram (already marked)")
            
            raise HTTPException(
                status_code=503,
                detail="Файл недоступен. Отправьте этот трек боту повторно, чтобы обновить ссылку."
            )
    
    # Generate secure temporary token with cached file_path
    token = generate_stream_token(track.id, user.id, file_path)
    
    # Return relative URL to avoid Mixed Content issues (HTTP vs HTTPS)
    # The frontend will resolve this against its own origin
    proxy_url = f"/api/player/audio/{token}"
    
    expires_at = int(time.time()) + STREAM_TOKEN_TTL
    
    # Log with info about whether we're using alternative
    if hd_track_info:
        logger.info(f"[Stream Request] Streaming MP3 track {track.id} (for HD {original_track.id}), user_id={user.id}")
    else:
        logger.info(f"[Stream Request] Generated token for track_id={track.id}, user_id={user.id}, file_size={track.file_size or 0} bytes")
    
    # Check if original track is MP3 and HD alternative exists
    hd_alt_info = None
    if hd_track_info is None and is_streamable(original_track.mime_type):
        # This is MP3 - check if HD version exists
        hd_alt = await find_hd_alternative(original_track, db)
        if hd_alt:
            hd_alt_info = {
                "id": hd_alt.id,
                "title": hd_alt.title,
            }
            logger.info(f"[Stream Request] HD alternative found for track {original_track.id}: HD track {hd_alt.id}")
    
    return StreamUrlResponse(
        url=proxy_url,
        expires_at=expires_at,
        track_id=track.id,
        # HD info: when playing MP3 alternative, tell about original HD
        # OR when playing MP3 and HD alternative exists
        hd_track_id=hd_track_info["id"] if hd_track_info else (hd_alt_info["id"] if hd_alt_info else None),
        hd_track_title=hd_track_info["title"] if hd_track_info else (hd_alt_info["title"] if hd_alt_info else None),
        is_hd_available=hd_track_info is not None or hd_alt_info is not None,
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
        logger.warning(f"[Audio Stream] Invalid/expired token: {token[:20]}...")
        raise HTTPException(status_code=401, detail="Invalid or expired stream token")
    
    track_id, user_id, file_path = token_data
    logger.debug(f"[Audio Stream] Token validated: track_id={track_id}, user_id={user_id}")
    
    # Get track for metadata (file_path already validated and cached in token)
    # Note: user_id in token is just for logging, access was validated when token was created
    track = await db.scalar(
        select(Track).where(Track.id == track_id)
    )
    
    if not track:
        logger.warning(f"[Audio Stream] Track not found: track_id={track_id}")
        raise HTTPException(status_code=404, detail="Track not found")
    
    # file_path is already in token - no need for second Telegram API call!
    if not file_path:
        logger.error(f"[Audio Stream] Empty file_path for track_id={track_id}")
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
    
    # Diagnostic: log stream start
    stream_start_time = time.time()
    expected_bytes = int(actual_content_length) if actual_content_length else 0
    logger.info(f"[Stream Start] track_id={track_id}, expected_bytes={expected_bytes}, range={range or 'full'}")
    
    async def stream_generator():
        """Stream audio from already-opened Telegram response with diagnostic logging"""
        bytes_sent = 0
        chunk_count = 0
        try:
            async for chunk in telegram_response.content.iter_chunked(64 * 1024):
                bytes_sent += len(chunk)
                chunk_count += 1
                yield chunk
            
            # Stream completed successfully
            elapsed = time.time() - stream_start_time
            speed_kbps = (bytes_sent / 1024) / elapsed if elapsed > 0 else 0
            logger.info(f"[Stream Complete] track_id={track_id}, bytes_sent={bytes_sent}, chunks={chunk_count}, elapsed={elapsed:.2f}s, speed={speed_kbps:.1f}KB/s")
            
        except asyncio.CancelledError:
            # Client disconnected (normal - seek, track change, etc.)
            elapsed = time.time() - stream_start_time
            logger.info(f"[Stream Cancelled] track_id={track_id}, bytes_sent={bytes_sent}/{expected_bytes}, elapsed={elapsed:.2f}s (client disconnected)")
            raise
            
        except aiohttp.ClientPayloadError as e:
            # Telegram closed connection unexpectedly
            elapsed = time.time() - stream_start_time
            logger.error(f"[Stream Error] track_id={track_id}, bytes_sent={bytes_sent}/{expected_bytes}, elapsed={elapsed:.2f}s, error=ClientPayloadError: {e}")
            raise
            
        except Exception as e:
            # Any other error
            elapsed = time.time() - stream_start_time
            logger.error(f"[Stream Error] track_id={track_id}, bytes_sent={bytes_sent}/{expected_bytes}, elapsed={elapsed:.2f}s, error={type(e).__name__}: {e}")
            raise
            
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
    
    # Get tracks (allow public tracks or tracks in user's library)
    from sqlalchemy import or_, exists
    
    # Subquery to check if user has track in their library
    user_has_track = (
        select(UserLibrary.id)
        .where(
            UserLibrary.track_id == Track.id,
            UserLibrary.user_id == user.id
        )
        .exists()
    )
    
    result = await db.execute(
        select(Track).where(
            Track.id.in_(track_ids),
            or_(
                Track.is_public == True,
                Track.uploader_id == user.id,
                user_has_track
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
    
    # Get tracks (allow public tracks or tracks in user's library)
    from sqlalchemy import or_, exists
    
    # Subquery to check if user has track in their library
    user_has_track = (
        select(UserLibrary.id)
        .where(
            UserLibrary.track_id == Track.id,
            UserLibrary.user_id == user.id
        )
        .exists()
    )
    
    result = await db.execute(
        select(Track).where(
            Track.id.in_(track_ids),
            or_(
                Track.is_public == True,
                Track.uploader_id == user.id,
                user_has_track
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
    
    if not track.is_public and track.uploader_id != user.id:
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
    
    if not track.is_public and track.uploader_id != user.id:
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
    
    # Get tracks (allow public tracks or tracks in user's library)
    from sqlalchemy import or_, exists
    
    # Subquery to check if user has track in their library
    user_has_track = (
        select(UserLibrary.id)
        .where(
            UserLibrary.track_id == Track.id,
            UserLibrary.user_id == user.id
        )
        .exists()
    )
    
    result = await db.execute(
        select(Track).where(
            Track.id.in_(request.track_ids),
            or_(
                Track.is_public == True,
                Track.uploader_id == user.id,
                user_has_track
            )
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


@router.get("/diagnostics")
async def get_player_diagnostics():
    """
    Get diagnostic information about player streaming system.
    Useful for debugging streaming issues.
    """
    global _http_session, _file_path_cache, _stream_tokens
    
    now = time.time()
    
    # Count active/expired tokens
    active_tokens = sum(1 for v in _stream_tokens.values() if v[3] > now)
    expired_tokens = len(_stream_tokens) - active_tokens
    
    # Count cached file paths
    active_paths = sum(1 for v in _file_path_cache.values() if v[1] > now)
    expired_paths = len(_file_path_cache) - active_paths
    
    # HTTP session stats
    session_stats = None
    if _http_session and not _http_session.closed:
        connector = _http_session.connector
        if connector:
            session_stats = {
                "closed": _http_session.closed,
                "limit": getattr(connector, '_limit', None),
                "limit_per_host": getattr(connector, '_limit_per_host', None),
            }
    
    # Test Telegram API connectivity
    telegram_status = "unknown"
    telegram_latency_ms = None
    try:
        session = await get_http_session()
        base_url = settings.telegram_api_url.rstrip('/')
        api_url = f"{base_url}/bot{settings.bot_token}/getMe"
        
        start = time.time()
        async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            telegram_latency_ms = round((time.time() - start) * 1000, 1)
            if resp.status == 200:
                data = await resp.json()
                if data.get("ok"):
                    telegram_status = "ok"
                else:
                    telegram_status = f"error: {data.get('description', 'unknown')}"
            else:
                telegram_status = f"http_{resp.status}"
    except asyncio.TimeoutError:
        telegram_status = "timeout"
    except Exception as e:
        telegram_status = f"error: {type(e).__name__}"
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "stream_tokens": {
            "active": active_tokens,
            "expired": expired_tokens,
            "ttl_seconds": STREAM_TOKEN_TTL,
        },
        "file_path_cache": {
            "active": active_paths,
            "expired": expired_paths,
            "ttl_seconds": FILE_PATH_CACHE_TTL,
        },
        "http_session": session_stats,
        "telegram_api": {
            "status": telegram_status,
            "latency_ms": telegram_latency_ms,
            "base_url": settings.telegram_api_url,
        }
    }
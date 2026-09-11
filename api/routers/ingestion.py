"""
TG Player API - External Music Ingestion Router
Provides endpoints for link preview, background import, and job tracking.
"""
import os
import re
import logging
import asyncio
import tempfile
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, status, Query
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile
from aiogram.client.default import DefaultBotProperties
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.config import get_settings
from shared.database import get_session, get_db
from shared.models import (
    User, Track, UserLibrary, AlbumTrack, LibrarySource,
    UserExternalAccount, UserChannel, ChannelMessage, ChannelMessageStatus, utcnow
)
from api.routers.auth import get_current_user, TelegramUser
from api.schemas.tracks import TrackResponse
from api.routers.library import track_to_response
from bot.services.tracks import track_service

from bot.services.ingestion import (
    provider_registry,
    job_manager,
    IngestionPipeline,
    JobStatus,
    EntityType,
    TrackMetadata,
)
from bot.services.ingestion.pipeline import _find_existing_track

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ingestion", tags=["ingestion"])
settings = get_settings()


class SearchItemResponse(BaseModel):
    provider: str
    url: str
    title: str
    artist: str
    duration: Optional[int] = None
    cover_url: Optional[str] = None
    external_id: Optional[str] = None
    in_library: bool = False
    in_channel: bool = False
    already_in_tg: bool = False
    track_id: Optional[int] = None


class QuickImportRequest(BaseModel):
    url: str
    title: Optional[str] = None
    artist: Optional[str] = None
    duration: Optional[int] = None
    cover_url: Optional[str] = None
    add_to_library: bool = False


class QuickImportResponse(BaseModel):
    track: TrackResponse
    already_existed: bool


class ExternalAccountResponse(BaseModel):
    provider: str
    username: str
    display_name: Optional[str] = None
    profile_url: Optional[str] = None
    avatar_url: Optional[str] = None
    likes_count: int = 0
    tracks_count: int = 0
    connected: bool = True
    last_synced_at: Optional[str] = None


class ConnectAccountRequest(BaseModel):
    username_or_url: str
    auth_token: Optional[str] = None


class SoundCloudLikeItem(BaseModel):
    url: str
    title: str
    artist: str
    duration: Optional[int] = None
    cover_url: Optional[str] = None
    in_library: bool = False
    in_channel: bool = False
    already_in_tg: bool = False
    track_id: Optional[int] = None
    liked_at: Optional[str] = None


class UserLikesResponse(BaseModel):
    provider: str
    account: ExternalAccountResponse
    total_likes: int
    items: List[SoundCloudLikeItem]
    next_cursor: Optional[str] = None



class TrackPreviewItem(BaseModel):
    url: str
    title: str
    artist: str
    duration: Optional[int] = None
    cover_url: Optional[str] = None
    in_library: bool = False
    already_in_tg: bool = False
    track_id: Optional[int] = None


class PreviewRequest(BaseModel):
    url: str


class PreviewResponse(BaseModel):
    provider: str
    entity_type: str
    url: str
    title: str
    author: Optional[str] = None
    cover_url: Optional[str] = None
    track_count: int = 1
    tracks: List[TrackPreviewItem] = []


class StartImportRequest(BaseModel):
    url: str
    selected_urls: Optional[List[str]] = None


class JobResponse(BaseModel):
    id: str
    user_id: int
    url: str
    provider_name: str
    entity_type: str
    title: str
    author: Optional[str] = None
    cover_url: Optional[str] = None
    total_tracks: int
    processed_tracks: int
    skipped_tracks: int
    failed_tracks: int
    current_track_title: Optional[str] = None
    status: str
    progress_percent: int
    error_message: Optional[str] = None
    playlist_id: Optional[int] = None
    imported_track_ids: List[int] = []
    selected_urls: Optional[List[str]] = None
    created_at: str
    updated_at: str


def _get_active_bot() -> Bot:
    """Retrieve active global Bot instance from api.main or create fallback."""
    import api.main
    if getattr(api.main, "api_bot", None):
        return api.main.api_bot
    return Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


async def _ensure_user_in_db(user: TelegramUser):
    """Ensure user exists in database."""
    async with get_session() as session:
        db_user = await session.get(User, user.id)
        if not db_user:
            db_user = User(
                id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )
            session.add(db_user)
            await session.commit()


@router.post("/preview", response_model=PreviewResponse)
async def preview_url(
    req: PreviewRequest,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Inspect an external music URL (SoundCloud, etc.) and return its metadata with tracks and library status."""
    url = req.url.strip()
    provider = provider_registry.find_provider(url)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported URL. Supported providers: {', '.join(provider_registry.list_providers())}",
        )

    try:
        entity = await provider.resolve_entity(url)
        tracks_meta = await provider.fetch_tracklist(entity)

        # Batch check against database
        # 1. Fetch all track IDs in this user's library
        user_lib_res = await db.execute(
            select(UserLibrary.track_id).where(UserLibrary.user_id == user.id)
        )
        user_track_ids = set(user_lib_res.scalars().all())

        preview_tracks: List[TrackPreviewItem] = []
        for t in tracks_meta:
            existing = await _find_existing_track(t.title, t.artist, t.duration, session=db)
            already_in_tg = existing is not None
            in_lib = (existing.id in user_track_ids) if existing else False
            existing_id = existing.id if existing else None

            preview_tracks.append(
                TrackPreviewItem(
                    url=t.url,
                    title=t.title,
                    artist=t.artist,
                    duration=t.duration,
                    cover_url=t.cover_url,
                    in_library=in_lib,
                    already_in_tg=already_in_tg,
                    track_id=existing_id,
                )
            )

        return PreviewResponse(
            provider=entity.provider_name,
            entity_type=entity.entity_type.value,
            url=entity.url,
            title=entity.title,
            author=entity.author,
            cover_url=entity.cover_url,
            track_count=len(preview_tracks) if preview_tracks else entity.track_count,
            tracks=preview_tracks,
        )
    except Exception as e:
        logger.error(f"Error resolving preview for {url}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not resolve link: {str(e)}",
        )


@router.post("/start", response_model=JobResponse)
async def start_import(
    req: StartImportRequest,
    user: TelegramUser = Depends(get_current_user),
):
    """Start an asynchronous background import of a track or playlist."""
    url = req.url.strip()
    provider = provider_registry.find_provider(url)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported music source URL",
        )

    await _ensure_user_in_db(user)

    try:
        entity = await provider.resolve_entity(url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to inspect URL: {str(e)}",
        )

    selected_urls = req.selected_urls
    total_tracks = len(selected_urls) if selected_urls else entity.track_count

    job = await job_manager.create_job(
        user_id=user.id,
        url=url,
        provider_name=provider.name,
        entity_type=entity.entity_type.value,
        title=entity.title,
        total_tracks=total_tracks,
        author=entity.author,
        cover_url=entity.cover_url,
        selected_urls=selected_urls,
    )

    bot = _get_active_bot()
    pipeline = IngestionPipeline(bot)

    # Spawn background task
    task = asyncio.create_task(pipeline.execute_job(job))
    job_manager.register_task(job.id, task)

    return JobResponse(**job.to_dict())


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    user: TelegramUser = Depends(get_current_user),
):
    """Check current status and progress of an import job."""
    job = job_manager.get_job(job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return JobResponse(**job.to_dict())


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    user: TelegramUser = Depends(get_current_user),
):
    """Cancel an ongoing import job."""
    job = job_manager.get_job(job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    cancelled = job_manager.cancel_job(job_id)
    return {"success": cancelled, "job_id": job_id, "status": job.status.value}


@router.get("/recent", response_model=List[JobResponse])
async def get_recent_jobs(
    user: TelegramUser = Depends(get_current_user),
):
    """List recent import jobs for the current user."""
    jobs = job_manager.get_user_jobs(user.id, limit=10)
    return [JobResponse(**j.to_dict()) for j in jobs]


@router.get("/search", response_model=List[SearchItemResponse])
async def search_external_tracks(
    q: str = Query(..., min_length=1),
    provider: str = Query("soundcloud"),
    limit: int = Query(30, ge=1, le=100),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search external music platforms (SoundCloud) by keyword with user library status."""
    prov = provider_registry.get_provider(provider)
    if not prov:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider '{provider}' not found",
        )

    results = await prov.search(q, limit=limit)
    if not results:
        return []

    # Batch check against database
    user_lib_res = await db.execute(
        select(UserLibrary.track_id).where(UserLibrary.user_id == user.id)
    )
    user_track_ids = set(user_lib_res.scalars().all())

    items: List[SearchItemResponse] = []
    for r in results:
        existing = await _find_existing_track(r.title, r.artist, r.duration, session=db)
        already_in_tg = existing is not None
        in_lib = (existing.id in user_track_ids) if existing else False
        existing_id = existing.id if existing else None

        items.append(
            SearchItemResponse(
                provider=r.provider_name,
                url=r.url,
                title=r.title,
                artist=r.artist,
                duration=r.duration,
                cover_url=r.cover_url,
                external_id=r.external_id,
                in_library=in_lib,
                already_in_tg=already_in_tg,
                track_id=existing_id,
            )
        )
    return items


@router.post("/quick-import", response_model=QuickImportResponse)
async def quick_import_track(
    req: QuickImportRequest,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    On-demand download & import of a single track from external search results.
    If already exists in DB, immediately links to library without downloading.
    Returns full TrackResponse so player can play it immediately.
    """
    await _ensure_user_in_db(user)

    # 1. Deduplication check
    existing_track = None
    if req.title and req.artist:
        existing_track = await _find_existing_track(req.title, req.artist, req.duration)

    if existing_track:
        if req.add_to_library:
            # Link to library if not already linked
            await track_service.save_track(
                user_id=user.id,
                file_id=existing_track.file_id,
                file_unique_id=existing_track.file_unique_id,
                title=existing_track.title,
                artist=existing_track.artist,
                duration=existing_track.duration,
                library_source=LibrarySource.UPLOADED,
                enrich=False,
                add_to_library=True,
            )

            # Auto-forward to user's Telegram backup channel if active
            try:
                from bot.services.channels import get_channel_service
                ch_svc = get_channel_service()
                if ch_svc:
                    await ch_svc.forward_track_to_channel(user.id, existing_track.id)
            except Exception as e:
                logger.debug(f"Quick-import channel forward failed for existing track: {e}")

        # Refresh track with relationships
        track_obj = await db.scalar(
            select(Track)
            .where(Track.id == existing_track.id)
            .options(
                selectinload(Track.enrichment),
                selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
            )
        )
        lib_entry = await db.scalar(
            select(UserLibrary)
            .where(UserLibrary.user_id == user.id, UserLibrary.track_id == existing_track.id)
        )
        return QuickImportResponse(
            track=track_to_response(track_obj, lib_entry),
            already_existed=True,
        )

    # 2. Download via provider
    provider = provider_registry.find_provider(req.url)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported track URL",
        )

    track_meta = TrackMetadata(
        provider_name=provider.name,
        url=req.url,
        title=req.title or "Track",
        artist=req.artist or "Artist",
        duration=req.duration,
        cover_url=req.cover_url,
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            downloaded = await provider.download_track(track_meta, temp_dir)
        except Exception as e:
            raw_err = str(e)
            clean_err = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', raw_err)
            clean_err = re.sub(r'^ERROR:\s*', '', clean_err).strip()

            if "drm protected" in clean_err.lower() or "защищён drm" in clean_err.lower():
                user_msg = "Этот трек защищён DRM (SoundCloud Go+) и недоступен для бесплатного воспроизведения."
                status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            else:
                user_msg = f"Не удалось загрузить трек: {clean_err}"
                status_code = status.HTTP_502_BAD_GATEWAY

            logger.error(f"Failed to download audio from {req.url}: {clean_err}")
            raise HTTPException(
                status_code=status_code,
                detail=user_msg,
            )

        if downloaded.file_size > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Track exceeds 50MB Telegram Bot API limit",
            )

        bot = _get_active_bot()
        target_chat = settings.scanner_buffer_chat_id or user.id

        safe_filename = f"{track_meta.artist} - {track_meta.title}.mp3".replace("/", "-")
        audio_input = FSInputFile(downloaded.audio_path, filename=safe_filename)
        thumb_input = None
        if downloaded.cover_path and os.path.exists(downloaded.cover_path):
            thumb_input = FSInputFile(downloaded.cover_path)

        try:
            sent_msg = await bot.send_audio(
                chat_id=target_chat,
                audio=audio_input,
                title=track_meta.title,
                performer=track_meta.artist,
                duration=track_meta.duration,
                thumbnail=thumb_input,
            )
        except Exception as e:
            clean_upload_err = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', str(e))
            logger.error(f"Failed to upload audio to Telegram: {clean_upload_err}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Telegram upload failed: {clean_upload_err}",
            )

        if not sent_msg or not sent_msg.audio:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload audio to Telegram",
            )

        save_res = await track_service.save_track(
            user_id=user.id,
            file_id=sent_msg.audio.file_id,
            file_unique_id=sent_msg.audio.file_unique_id,
            title=track_meta.title,
            artist=track_meta.artist,
            duration=sent_msg.audio.duration or track_meta.duration,
            file_size=sent_msg.audio.file_size or downloaded.file_size,
            mime_type=sent_msg.audio.mime_type or "audio/mpeg",
            file_name=safe_filename,
            library_source=LibrarySource.UPLOADED,
            enrich=True,
            add_to_library=req.add_to_library,
        )

        # Auto-forward to user's Telegram backup channel ONLY if add_to_library is True
        if req.add_to_library:
            try:
                from bot.services.channels import get_channel_service
                ch_svc = get_channel_service()
                if ch_svc:
                    await ch_svc.forward_track_to_channel(user.id, save_res.track_id)
            except Exception as e:
                logger.debug(f"Quick-import channel forward failed for new track: {e}")

        track_obj = await db.scalar(
            select(Track)
            .where(Track.id == save_res.track_id)
            .options(
                selectinload(Track.enrichment),
                selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
            )
        )
        lib_entry = await db.scalar(
            select(UserLibrary)
            .where(UserLibrary.user_id == user.id, UserLibrary.track_id == save_res.track_id)
        )

        return QuickImportResponse(
            track=track_to_response(track_obj, lib_entry),
            already_existed=False,
        )


# ============== Connected External Accounts (SoundCloud) ==============

@router.get("/account/soundcloud")
async def get_soundcloud_account(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get connected SoundCloud account for current user."""
    account = await db.scalar(
        select(UserExternalAccount)
        .where(UserExternalAccount.user_id == user.id, UserExternalAccount.provider == "soundcloud")
    )
    if not account:
        return {"connected": False}

    return ExternalAccountResponse(
        provider=account.provider,
        username=account.username,
        display_name=account.display_name,
        profile_url=account.profile_url,
        avatar_url=account.avatar_url,
        likes_count=account.likes_count,
        tracks_count=account.tracks_count,
        connected=True,
        last_synced_at=account.last_synced_at.isoformat() if account.last_synced_at else None,
    )


@router.post("/account/soundcloud/connect", response_model=ExternalAccountResponse)
async def connect_soundcloud_account(
    req: ConnectAccountRequest,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Connect a SoundCloud profile to user account."""
    sc_provider = provider_registry.get_provider("soundcloud")
    if not sc_provider:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SoundCloud provider unavailable",
        )

    await _ensure_user_in_db(user)

    try:
        profile = await sc_provider.resolve_user_profile(req.username_or_url, req.auth_token)
    except Exception as e:
        logger.warning(f"Failed to resolve SoundCloud profile '{req.username_or_url}': {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Не удалось подключить профиль SoundCloud: {str(e)}",
        )

    account = await db.scalar(
        select(UserExternalAccount)
        .where(UserExternalAccount.user_id == user.id, UserExternalAccount.provider == "soundcloud")
    )

    if not account:
        account = UserExternalAccount(
            user_id=user.id,
            provider="soundcloud",
            external_id=profile.get("external_id"),
            username=profile["username"],
            display_name=profile.get("display_name"),
            profile_url=profile.get("profile_url"),
            avatar_url=profile.get("avatar_url"),
            auth_token=req.auth_token,
            likes_count=profile.get("likes_count", 0),
            tracks_count=profile.get("tracks_count", 0),
            last_synced_at=utcnow(),
        )
        db.add(account)
    else:
        account.external_id = profile.get("external_id")
        account.username = profile["username"]
        account.display_name = profile.get("display_name")
        account.profile_url = profile.get("profile_url")
        account.avatar_url = profile.get("avatar_url")
        account.likes_count = profile.get("likes_count", 0)
        account.tracks_count = profile.get("tracks_count", 0)
        if req.auth_token:
            account.auth_token = req.auth_token
        account.last_synced_at = utcnow()

    await db.commit()
    await db.refresh(account)

    return ExternalAccountResponse(
        provider=account.provider,
        username=account.username,
        display_name=account.display_name,
        profile_url=account.profile_url,
        avatar_url=account.avatar_url,
        likes_count=account.likes_count,
        tracks_count=account.tracks_count,
        connected=True,
        last_synced_at=account.last_synced_at.isoformat() if account.last_synced_at else None,
    )


@router.delete("/account/soundcloud")
async def disconnect_soundcloud_account(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect SoundCloud account."""
    account = await db.scalar(
        select(UserExternalAccount)
        .where(UserExternalAccount.user_id == user.id, UserExternalAccount.provider == "soundcloud")
    )
    if account:
        await db.delete(account)
        await db.commit()
    return {"ok": True, "message": "SoundCloud аккаунт отключен"}


@router.get("/account/soundcloud/likes", response_model=UserLikesResponse)
async def get_soundcloud_likes(
    limit: int = Query(40, ge=1, le=100),
    cursor: Optional[str] = None,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch user's liked tracks from SoundCloud with local library & channel backup status."""
    account = await db.scalar(
        select(UserExternalAccount)
        .where(UserExternalAccount.user_id == user.id, UserExternalAccount.provider == "soundcloud")
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SoundCloud аккаунт не подключен. Перейдите в настройки для подключения.",
        )

    sc_provider = provider_registry.get_provider("soundcloud")
    if not sc_provider:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SoundCloud provider unavailable",
        )

    try:
        ident = account.external_id or account.username
        tracks_meta, next_cursor = await sc_provider.fetch_user_likes(
            ident, limit=limit, next_href=cursor, auth_token=account.auth_token
        )
    except Exception as e:
        logger.error(f"Failed to fetch SoundCloud likes for {account.username}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Не удалось получить лайки с SoundCloud: {str(e)}",
        )

    # Preload user's library and channel backup status in batch
    user_lib_q = select(UserLibrary.track_id).where(UserLibrary.user_id == user.id)
    user_lib_track_ids = set((await db.scalars(user_lib_q)).all())

    user_ch_q = (
        select(ChannelMessage.track_id)
        .join(UserChannel, ChannelMessage.channel_id == UserChannel.id)
        .where(UserChannel.user_id == user.id, ChannelMessage.status == ChannelMessageStatus.SENT)
    )
    user_channel_track_ids = set((await db.scalars(user_ch_q)).all())

    items: List[SoundCloudLikeItem] = []
    for t in tracks_meta:
        existing = await _find_existing_track(t.title, t.artist, t.duration, session=db)
        already_in_tg = existing is not None
        in_lib = (existing.id in user_lib_track_ids) if existing else False
        in_chan = (existing.id in user_channel_track_ids) if existing else False
        existing_id = existing.id if existing else None

        items.append(
            SoundCloudLikeItem(
                url=t.url,
                title=t.title,
                artist=t.artist,
                duration=t.duration,
                cover_url=t.cover_url,
                in_library=in_lib,
                in_channel=in_chan,
                already_in_tg=already_in_tg,
                track_id=existing_id,
                liked_at=t.extra.get("liked_at") if t.extra else None,
            )
        )

    account_resp = ExternalAccountResponse(
        provider=account.provider,
        username=account.username,
        display_name=account.display_name,
        profile_url=account.profile_url,
        avatar_url=account.avatar_url,
        likes_count=account.likes_count,
        tracks_count=account.tracks_count,
        connected=True,
        last_synced_at=account.last_synced_at.isoformat() if account.last_synced_at else None,
    )

    return UserLikesResponse(
        provider="soundcloud",
        account=account_resp,
        total_likes=account.likes_count,
        items=items,
        next_cursor=next_cursor,
    )


# ============== Connected External Accounts (Spotify) ==============

@router.get("/account/spotify")
async def get_spotify_account(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get connected Spotify account for current user."""
    account = await db.scalar(
        select(UserExternalAccount)
        .where(UserExternalAccount.user_id == user.id, UserExternalAccount.provider == "spotify")
    )
    if not account:
        return {"connected": False}

    return ExternalAccountResponse(
        provider=account.provider,
        username=account.username,
        display_name=account.display_name,
        profile_url=account.profile_url,
        avatar_url=account.avatar_url,
        likes_count=account.likes_count,
        tracks_count=account.tracks_count,
        connected=True,
        last_synced_at=account.last_synced_at.isoformat() if account.last_synced_at else None,
    )


@router.post("/account/spotify/connect", response_model=ExternalAccountResponse)
async def connect_spotify_account(
    req: ConnectAccountRequest,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Connect a Spotify account or sp_dc session token."""
    sp_provider = provider_registry.get_provider("spotify")
    if not sp_provider:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Spotify provider unavailable",
        )

    await _ensure_user_in_db(user)

    try:
        profile = await sp_provider.resolve_user_profile(req.username_or_url, req.auth_token)
    except Exception as e:
        logger.warning(f"Failed to resolve Spotify profile '{req.username_or_url}': {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Не удалось подключить профиль Spotify: {str(e)}",
        )

    account = await db.scalar(
        select(UserExternalAccount)
        .where(UserExternalAccount.user_id == user.id, UserExternalAccount.provider == "spotify")
    )

    if not account:
        account = UserExternalAccount(
            user_id=user.id,
            provider="spotify",
            external_id=profile.get("external_id"),
            username=profile["username"],
            display_name=profile.get("display_name"),
            profile_url=profile.get("profile_url"),
            avatar_url=profile.get("avatar_url"),
            auth_token=req.auth_token,
            likes_count=profile.get("likes_count", 0),
            tracks_count=profile.get("tracks_count", 0),
            last_synced_at=utcnow(),
        )
        db.add(account)
    else:
        account.external_id = profile.get("external_id")
        account.username = profile["username"]
        account.display_name = profile.get("display_name")
        account.profile_url = profile.get("profile_url")
        account.avatar_url = profile.get("avatar_url")
        account.likes_count = profile.get("likes_count", 0)
        account.tracks_count = profile.get("tracks_count", 0)
        if req.auth_token:
            account.auth_token = req.auth_token
        account.last_synced_at = utcnow()

    await db.commit()
    await db.refresh(account)

    return ExternalAccountResponse(
        provider=account.provider,
        username=account.username,
        display_name=account.display_name,
        profile_url=account.profile_url,
        avatar_url=account.avatar_url,
        likes_count=account.likes_count,
        tracks_count=account.tracks_count,
        connected=True,
        last_synced_at=account.last_synced_at.isoformat() if account.last_synced_at else None,
    )


@router.delete("/account/spotify")
async def disconnect_spotify_account(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect Spotify account."""
    account = await db.scalar(
        select(UserExternalAccount)
        .where(UserExternalAccount.user_id == user.id, UserExternalAccount.provider == "spotify")
    )
    if account:
        await db.delete(account)
        await db.commit()
    return {"ok": True, "message": "Spotify аккаунт отключен"}


@router.get("/account/spotify/likes", response_model=UserLikesResponse)
async def get_spotify_likes(
    limit: int = Query(40, ge=1, le=50),
    cursor: Optional[str] = None,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch user's liked tracks from Spotify with local library & channel backup status."""
    account = await db.scalar(
        select(UserExternalAccount)
        .where(UserExternalAccount.user_id == user.id, UserExternalAccount.provider == "spotify")
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spotify аккаунт не подключен. Перейдите в настройки для подключения.",
        )

    sp_provider = provider_registry.get_provider("spotify")
    if not sp_provider:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Spotify provider unavailable",
        )

    try:
        ident = account.external_id or account.username
        tracks_meta, next_cursor = await sp_provider.fetch_user_likes(
            ident, limit=limit, next_href=cursor, auth_token=account.auth_token
        )
    except Exception as e:
        logger.error(f"Failed to fetch Spotify likes for {account.username}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Не удалось получить лайки со Spotify: {str(e)}",
        )

    # Preload user's library and channel backup status in batch
    user_lib_q = select(UserLibrary.track_id).where(UserLibrary.user_id == user.id)
    user_lib_track_ids = set((await db.scalars(user_lib_q)).all())

    user_ch_q = (
        select(ChannelMessage.track_id)
        .join(UserChannel, ChannelMessage.channel_id == UserChannel.id)
        .where(UserChannel.user_id == user.id, ChannelMessage.status == ChannelMessageStatus.SENT)
    )
    user_channel_track_ids = set((await db.scalars(user_ch_q)).all())

    items: List[SoundCloudLikeItem] = []
    for t in tracks_meta:
        existing = await _find_existing_track(t.title, t.artist, t.duration, session=db)
        already_in_tg = existing is not None
        in_lib = (existing.id in user_lib_track_ids) if existing else False
        in_chan = (existing.id in user_channel_track_ids) if existing else False
        existing_id = existing.id if existing else None

        items.append(
            SoundCloudLikeItem(
                url=t.url,
                title=t.title,
                artist=t.artist,
                duration=t.duration,
                cover_url=t.cover_url,
                in_library=in_lib,
                in_channel=in_chan,
                already_in_tg=already_in_tg,
                track_id=existing_id,
                liked_at=t.extra.get("liked_at") if t.extra else None,
            )
        )

    account_resp = ExternalAccountResponse(
        provider=account.provider,
        username=account.username,
        display_name=account.display_name,
        profile_url=account.profile_url,
        avatar_url=account.avatar_url,
        likes_count=account.likes_count,
        tracks_count=account.tracks_count,
        connected=True,
        last_synced_at=account.last_synced_at.isoformat() if account.last_synced_at else None,
    )

    return UserLikesResponse(
        provider="spotify",
        account=account_resp,
        total_likes=account.likes_count,
        items=items,
        next_cursor=next_cursor,
    )


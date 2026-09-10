"""
TG Player API - External Music Ingestion Router
Provides endpoints for link preview, background import, and job tracking.
"""
import os
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
from shared.models import User, Track, UserLibrary, AlbumTrack, LibrarySource
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


class QuickImportRequest(BaseModel):
    url: str
    title: Optional[str] = None
    artist: Optional[str] = None
    duration: Optional[int] = None
    cover_url: Optional[str] = None


class QuickImportResponse(BaseModel):
    track: TrackResponse
    already_existed: bool


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


class StartImportRequest(BaseModel):
    url: str


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
):
    """Inspect an external music URL (SoundCloud, etc.) and return its metadata without importing."""
    url = req.url.strip()
    provider = provider_registry.find_provider(url)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported URL. Supported providers: {', '.join(provider_registry.list_providers())}",
        )

    try:
        entity = await provider.resolve_entity(url)
        return PreviewResponse(
            provider=entity.provider_name,
            entity_type=entity.entity_type.value,
            url=entity.url,
            title=entity.title,
            author=entity.author,
            cover_url=entity.cover_url,
            track_count=entity.track_count,
        )
    except Exception as e:
        logger.error(f"Error resolving preview for {url}: {e}")
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

    job = await job_manager.create_job(
        user_id=user.id,
        url=url,
        provider_name=provider.name,
        entity_type=entity.entity_type.value,
        title=entity.title,
        total_tracks=entity.track_count,
        author=entity.author,
        cover_url=entity.cover_url,
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
    limit: int = Query(15, ge=1, le=50),
    user: TelegramUser = Depends(get_current_user),
):
    """Search external music platforms (SoundCloud) by keyword."""
    prov = provider_registry.get_provider(provider)
    if not prov:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider '{provider}' not found",
        )

    results = await prov.search(q, limit=limit)
    return [
        SearchItemResponse(
            provider=r.provider_name,
            url=r.url,
            title=r.title,
            artist=r.artist,
            duration=r.duration,
            cover_url=r.cover_url,
            external_id=r.external_id,
        )
        for r in results
    ]


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
        )

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
            logger.error(f"Failed to download audio from {req.url}: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Could not download track: {str(e)}",
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
            logger.error(f"Failed to upload audio to Telegram: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Telegram upload failed: {str(e)}",
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
        )

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

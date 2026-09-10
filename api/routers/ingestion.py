"""
TG Player API - External Music Ingestion Router
Provides endpoints for link preview, background import, and job tracking.
"""
import logging
import asyncio
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, status
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from shared.config import get_settings
from shared.database import get_session
from shared.models import User
from api.routers.auth import get_current_user, TelegramUser

from bot.services.ingestion import (
    provider_registry,
    job_manager,
    IngestionPipeline,
    JobStatus,
    EntityType,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ingestion", tags=["ingestion"])
settings = get_settings()


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

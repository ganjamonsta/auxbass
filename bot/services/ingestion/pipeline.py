"""
TG Player - Ingestion Pipeline
Orchestrates downloading, deduplication, Telegram upload, and database registration.
"""
import os
import shutil
import logging
import asyncio
import re
import tempfile
from datetime import datetime, timezone
from typing import Optional, Callable, Any, List, Dict

from aiogram import Bot
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest
from sqlalchemy import select, and_, or_

from shared.config import get_settings
from shared.database import get_session
from shared.models import Track, Playlist, PlaylistTrack, UserLibrary, LibrarySource
from shared.matching import normalize_artist, clean_track_metadata

from bot.services.tracks import track_service
from .base import TrackMetadata, EntityType, SourceEntity
from .job_manager import IngestionJob, JobStatus, job_manager
from .registry import provider_registry

logger = logging.getLogger(__name__)
settings = get_settings()


async def _find_existing_track(
    title: str,
    artist: str,
    duration: Optional[int],
    session: Optional[Any] = None,
) -> Optional[Track]:
    """Check if track with matching title & artist already exists in global library."""
    clean_title, clean_artist = clean_track_metadata(title, artist)
    norm_artist = normalize_artist(clean_artist)

    async def _execute_lookup(s):
        query = select(Track).where(
            and_(
                Track.normalized_artist == norm_artist,
                Track.title.ilike(clean_title),
                Track.is_unavailable == False,
            )
        )
        result = await s.execute(query)
        candidates = result.scalars().all()

        if not candidates:
            # Try without exact artist normalization (case-insensitive search)
            query2 = select(Track).where(
                and_(
                    Track.artist.ilike(clean_artist),
                    Track.title.ilike(clean_title),
                    Track.is_unavailable == False,
                )
            )
            result2 = await s.execute(query2)
            candidates = result2.scalars().all()

        if not candidates:
            return None

        # If duration provided, find the closest match within ±5 seconds
        if duration:
            for t in candidates:
                if t.duration and abs(t.duration - duration) <= 5:
                    return t

        return candidates[0]

    if session:
        return await _execute_lookup(session)
    async with get_session() as new_session:
        return await _execute_lookup(new_session)


class IngestionPipeline:
    """Executes an IngestionJob end-to-end."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def execute_job(
        self,
        job: IngestionJob,
        progress_callback: Optional[Callable[[IngestionJob], Any]] = None,
    ):
        """Run the full ingestion pipeline for a given job."""
        job.status = JobStatus.IN_PROGRESS
        job.updated_at = datetime.now(timezone.utc)
        if progress_callback:
            await progress_callback(job)

        provider = provider_registry.get_provider(job.provider_name)
        if not provider:
            job.status = JobStatus.FAILED
            job.error_message = f"Unknown provider: {job.provider_name}"
            job.updated_at = datetime.now(timezone.utc)
            if progress_callback:
                await progress_callback(job)
            return

        try:
            entity = SourceEntity(
                provider_name=job.provider_name,
                entity_type=EntityType(job.entity_type),
                url=job.url,
                title=job.title,
                author=job.author,
                cover_url=job.cover_url,
                track_count=job.total_tracks,
            )

            # 1. Fetch full tracklist
            tracks_meta = await provider.fetch_tracklist(entity)
            if not tracks_meta:
                job.status = JobStatus.FAILED
                job.error_message = "No tracks found at this URL"
                job.updated_at = datetime.now(timezone.utc)
                if progress_callback:
                    await progress_callback(job)
                return

            # Filter tracks if user made a selective import
            if job.selected_urls:
                selected_set = set(job.selected_urls)
                tracks_meta = [t for t in tracks_meta if t.url in selected_set]
                if not tracks_meta:
                    job.status = JobStatus.FAILED
                    job.error_message = "No matching selected tracks found"
                    job.updated_at = datetime.now(timezone.utc)
                    if progress_callback:
                        await progress_callback(job)
                    return

            job.total_tracks = len(tracks_meta)
            job.updated_at = datetime.now(timezone.utc)
            if progress_callback:
                await progress_callback(job)

            # 2. If it's a playlist or album, create a playlist record in Auxbass
            if job.entity_type in (EntityType.PLAYLIST.value, EntityType.ALBUM.value) and not job.playlist_id:
                async with get_session() as session:
                    playlist = Playlist(
                        owner_id=job.user_id,
                        name=job.title,
                        description=f"Imported from {job.provider_name.title()}: {job.url}",
                        cover_url=job.cover_url,
                        is_public=False,
                    )
                    session.add(playlist)
                    await session.commit()
                    await session.refresh(playlist)
                    job.playlist_id = playlist.id

            # 3. Target chat for bot upload
            # If buffer chat is configured, send there to avoid spamming the user's DM.
            # Otherwise send to the user's chat.
            target_chat_id = settings.scanner_buffer_chat_id or job.user_id

            # 4. Ingest each track
            for idx, track_meta in enumerate(tracks_meta):
                if job.status == JobStatus.CANCELLED:
                    logger.info(f"Ingestion job {job.id} cancelled by user.")
                    break

                job.current_track_title = f"{track_meta.artist} - {track_meta.title}"
                job.updated_at = datetime.now(timezone.utc)
                if progress_callback:
                    await progress_callback(job)

                try:
                    # A. Deduplication check: exists globally?
                    existing = await _find_existing_track(
                        track_meta.title, track_meta.artist, track_meta.duration
                    )

                    if existing:
                        logger.info(f"[Ingestion] Found existing track {existing.id} ({existing.artist} - {existing.title})")
                        # Add existing track to user's library
                        await track_service.save_track(
                            user_id=job.user_id,
                            file_id=existing.file_id,
                            file_unique_id=existing.file_unique_id,
                            title=existing.title,
                            artist=existing.artist,
                            duration=existing.duration,
                            library_source=LibrarySource.UPLOADED,
                            enrich=False,
                        )

                        # Add to playlist if playlist import
                        if job.playlist_id:
                            await self._add_track_to_playlist(job.playlist_id, existing.id, len(job.imported_track_ids) + 1)

                        # Auto-forward to user's Telegram backup channel if active
                        try:
                            from bot.services.channels import get_channel_service
                            ch_svc = get_channel_service()
                            if ch_svc:
                                await ch_svc.forward_track_to_channel(job.user_id, existing.id)
                        except Exception as e:
                            logger.debug(f"[Ingestion] Channel forward skipped for existing track {existing.id}: {e}")

                        job.imported_track_ids.append(existing.id)
                        job.skipped_tracks += 1
                        job.processed_tracks += 1
                        job.updated_at = datetime.now(timezone.utc)
                        if progress_callback:
                            await progress_callback(job)
                        continue

                    # B. Download audio to temporary directory
                    with tempfile.TemporaryDirectory() as temp_dir:
                        downloaded = await provider.download_track(track_meta, temp_dir)

                        # Check Telegram 50MB limit
                        if downloaded.file_size > 50 * 1024 * 1024:
                            logger.warning(f"[Ingestion] File {downloaded.audio_path} exceeds 50MB ({downloaded.file_size} bytes). Skipping.")
                            job.failed_tracks += 1
                            job.processed_tracks += 1
                            continue

                        # C. Upload to Telegram
                        safe_filename = f"{track_meta.artist} - {track_meta.title}.mp3".replace("/", "-")
                        audio_input = FSInputFile(downloaded.audio_path, filename=safe_filename)
                        thumb_input = None
                        if downloaded.cover_path and os.path.exists(downloaded.cover_path):
                            thumb_input = FSInputFile(downloaded.cover_path)

                        sent_msg = None
                        retry_attempts = 3
                        while retry_attempts > 0:
                            try:
                                sent_msg = await self.bot.send_audio(
                                    chat_id=target_chat_id,
                                    audio=audio_input,
                                    title=track_meta.title,
                                    performer=track_meta.artist,
                                    duration=track_meta.duration,
                                    thumbnail=thumb_input,
                                )
                                break
                            except TelegramRetryAfter as e:
                                logger.warning(f"[Ingestion] Flood control hit: wait {e.retry_after}s")
                                await asyncio.sleep(e.retry_after + 1)
                                retry_attempts -= 1
                            except TelegramBadRequest as e:
                                logger.error(f"[Ingestion] Bad request uploading audio: {e}")
                                break

                        if not sent_msg or not sent_msg.audio:
                            job.failed_tracks += 1
                            job.processed_tracks += 1
                            continue

                        # D. Register in database & trigger enrichment
                        save_result = await track_service.save_track(
                            user_id=job.user_id,
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

                        # E. Add to playlist
                        if job.playlist_id:
                            await self._add_track_to_playlist(job.playlist_id, save_result.track_id, len(job.imported_track_ids) + 1)

                        # Auto-forward to user's Telegram backup channel if active
                        try:
                            from bot.services.channels import get_channel_service
                            ch_svc = get_channel_service()
                            if ch_svc:
                                await ch_svc.forward_track_to_channel(job.user_id, save_result.track_id)
                        except Exception as e:
                            logger.debug(f"[Ingestion] Channel forward failed for new track {save_result.track_id}: {e}")

                        job.imported_track_ids.append(save_result.track_id)
                        job.processed_tracks += 1
                        job.updated_at = datetime.now(timezone.utc)
                        if progress_callback:
                            await progress_callback(job)

                    # F. Telegram flood delay between tracks
                    if idx < len(tracks_meta) - 1:
                        await asyncio.sleep(1.5)

                except Exception as e:
                    clean_msg = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', str(e))
                    if "drm protected" in clean_msg.lower() or "защищён drm" in clean_msg.lower():
                        logger.warning(f"[Ingestion] Skipped DRM protected track {track_meta.title}: {clean_msg}")
                    else:
                        logger.error(f"[Ingestion] Failed to import track {track_meta.title}: {clean_msg}")
                    job.failed_tracks += 1
                    job.processed_tracks += 1

            # Done processing all tracks
            if job.status != JobStatus.CANCELLED:
                job.status = JobStatus.COMPLETED
                job.current_track_title = None
                job.updated_at = datetime.now(timezone.utc)
                if progress_callback:
                    await progress_callback(job)

        except Exception as e:
            logger.error(f"[Ingestion] Job {job.id} failed with unhandled error: {e}", exc_info=True)
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.updated_at = datetime.now(timezone.utc)
            if progress_callback:
                await progress_callback(job)

    async def _add_track_to_playlist(self, playlist_id: int, track_id: int, position: int):
        """Associate imported track with the created playlist."""
        try:
            async with get_session() as session:
                # Ensure it's not already in playlist
                existing = await session.execute(
                    select(PlaylistTrack).where(
                        and_(
                            PlaylistTrack.playlist_id == playlist_id,
                            PlaylistTrack.track_id == track_id,
                        )
                    )
                )
                if not existing.scalar():
                    pt = PlaylistTrack(
                        playlist_id=playlist_id,
                        track_id=track_id,
                        position=position,
                    )
                    session.add(pt)
                    await session.commit()
        except Exception as e:
            logger.warning(f"[Ingestion] Failed to link track {track_id} to playlist {playlist_id}: {e}")

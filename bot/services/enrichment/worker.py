"""
TG Player - Background Enrichment Worker

Periodically processes tracks with pending enrichment status.
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy import select, func

from shared.database import get_session
from shared.models import Track, TrackEnrichment, EnrichmentStatus, utcnow
from .processor import enrichment_processor, EnrichmentResult

logger = logging.getLogger(__name__)


class EnrichmentWorker:
    """Background worker for automatic track enrichment"""
    
    def __init__(self):
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._stats = {
            "processed": 0,
            "success": 0,
            "failed": 0,
        }
        
        # Callbacks
        self._on_enrichment_complete = None
    
    def set_on_enrichment_complete(self, callback):
        """
        Set callback to be called when track enrichment completes.
        Callback signature: async def callback(track_id: int, result: EnrichmentResult)
        """
        self._on_enrichment_complete = callback
    
    async def start(self, idle_interval: int = 60, busy_interval: int = 5):
        """
        Start background enrichment loop.
        
        Args:
            idle_interval: Seconds to wait when no pending tracks
            busy_interval: Seconds to wait when processing tracks
        """
        if self.running:
            return
        
        self.running = True
        self._task = asyncio.create_task(
            self._worker_loop(idle_interval, busy_interval)
        )
        logger.info("Enrichment worker started")
    
    async def stop(self):
        """Stop background enrichment"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        await enrichment_processor.close()
        logger.info("Enrichment worker stopped")
    
    async def _worker_loop(self, idle_interval: int, busy_interval: int):
        """Main worker loop"""
        while self.running:
            try:
                had_work = await self._process_batch()
                
                # Adaptive interval
                interval = busy_interval if had_work else idle_interval
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Enrichment worker error: {e}")
                await asyncio.sleep(idle_interval)
    
    async def _process_batch(self, batch_size: int = 10) -> bool:
        """
        Process a batch of pending tracks.
        
        Returns:
            True if there was work to do
        """
        async with get_session() as session:
            # Get pending tracks - prioritize newest tracks (higher id = newer)
            result = await session.execute(
                select(Track)
                .where(Track.enrichment_status == EnrichmentStatus.PENDING)
                .order_by(Track.id.desc())
                .limit(batch_size)
            )
            tracks = list(result.scalars().all())
            
            if not tracks:
                return False
            
            logger.info(f"Processing {len(tracks)} tracks for enrichment")
            
            # Mark as processing
            for track in tracks:
                track.enrichment_status = EnrichmentStatus.PROCESSING
            await session.flush()
        
        # Process each track (outside of main session to avoid long locks)
        for track in tracks:
            await self._enrich_track(track.id, track.title, track.artist)
        
        self._stats["processed"] += len(tracks)
        return True
    
    async def _enrich_track(self, track_id: int, title: str, artist: str):
        """Enrich a single track"""
        try:
            # Get enrichment data
            result = await enrichment_processor.enrich_track(title, artist or "")
            
            async with get_session() as session:
                track = await session.get(Track, track_id)
                if not track:
                    return
                
                if result.success:
                    # Create or update enrichment record
                    enrichment = await session.scalar(
                        select(TrackEnrichment)
                        .where(TrackEnrichment.track_id == track_id)
                    )
                    
                    if not enrichment:
                        enrichment = TrackEnrichment(track_id=track_id)
                        session.add(enrichment)
                    
                    # Update enrichment data
                    if result.album_name:
                        enrichment.album_name = result.album_name
                    if result.genre:
                        enrichment.genre = result.genre
                    if result.tags:
                        enrichment.tags = result.tags
                    if result.cover_url:
                        enrichment.cover_url = result.cover_url
                    if result.release_date:
                        enrichment.release_date = result.release_date
                    if result.track_number:
                        enrichment.track_number = result.track_number
                    if result.deezer_track_id:
                        enrichment.deezer_track_id = result.deezer_track_id
                    if result.deezer_album_id:
                        enrichment.deezer_album_id = result.deezer_album_id
                    if result.lastfm_url:
                        enrichment.lastfm_url = result.lastfm_url
                    
                    enrichment.confidence = result.confidence
                    enrichment.enriched_at = utcnow()
                    
                    track.enrichment_status = EnrichmentStatus.COMPLETED
                    self._stats["success"] += 1
                    
                    logger.info(f"Enriched track {track_id}: {title} - {artist}")
                else:
                    track.enrichment_status = EnrichmentStatus.FAILED
                    self._stats["failed"] += 1
                    logger.debug(f"No enrichment data for track {track_id}")
            
            # Call completion callback
            if self._on_enrichment_complete:
                try:
                    await self._on_enrichment_complete(track_id, result)
                except Exception as e:
                    logger.error(f"Enrichment callback error: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to enrich track {track_id}: {e}")
            
            async with get_session() as session:
                track = await session.get(Track, track_id)
                if track:
                    track.enrichment_status = EnrichmentStatus.FAILED
    
    async def get_stats(self) -> dict:
        """Get enrichment statistics"""
        async with get_session() as session:
            # Count by status
            result = await session.execute(
                select(Track.enrichment_status, func.count(Track.id))
                .group_by(Track.enrichment_status)
            )
            
            status_counts = {
                status.value if isinstance(status, EnrichmentStatus) else status: count 
                for status, count in result.all()
            }
            
            return {
                "pending": status_counts.get("pending", 0),
                "processing": status_counts.get("processing", 0),
                "completed": status_counts.get("completed", 0),
                "failed": status_counts.get("failed", 0),
                "total": sum(status_counts.values()),
                "session_processed": self._stats["processed"],
                "session_success": self._stats["success"],
                "session_failed": self._stats["failed"],
            }
    
    async def retry_failed(self) -> int:
        """
        Reset failed tracks to pending for retry.
        
        Returns:
            Number of tracks reset
        """
        async with get_session() as session:
            result = await session.execute(
                select(Track)
                .where(Track.enrichment_status == EnrichmentStatus.FAILED)
            )
            tracks = result.scalars().all()
            
            for track in tracks:
                track.enrichment_status = EnrichmentStatus.PENDING
            
            count = len(tracks)
            logger.info(f"Reset {count} failed tracks to pending")
            return count
    
    async def enrich_single(self, track_id: int) -> bool:
        """
        Manually trigger enrichment for a single track.
        
        Returns:
            True if enrichment was successful
        """
        async with get_session() as session:
            track = await session.get(Track, track_id)
            if not track:
                return False
            
            title = track.title
            artist = track.artist
            track.enrichment_status = EnrichmentStatus.PROCESSING
        
        await self._enrich_track(track_id, title, artist)
        
        async with get_session() as session:
            track = await session.get(Track, track_id)
            return track.enrichment_status == EnrichmentStatus.COMPLETED if track else False


# Global instance
enrichment_worker = EnrichmentWorker()

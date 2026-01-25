"""
TG Player - Background Enrichment Worker
Periodically enriches tracks with missing metadata
"""
import asyncio
import logging
from typing import Optional
from sqlalchemy import select, func

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import get_session
from shared.models import Track
from .metadata import metadata_service
from .albums import album_service

logger = logging.getLogger(__name__)


class EnrichmentWorker:
    """Background worker for metadata enrichment"""
    
    def __init__(self):
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._enrichment_count = 0  # Count enrichments for album assembly trigger
        self._album_assembly_threshold = 5  # Assemble albums every N enrichments
        self.stats = {
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
        }
    
    async def start(self, interval: int = 60):
        """Start background enrichment loop"""
        if self.running:
            return
        
        self.running = True
        self._task = asyncio.create_task(self._worker_loop(interval))
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
        await metadata_service.close()
        logger.info("Enrichment worker stopped")
    
    async def _worker_loop(self, interval: int):
        """Main worker loop with adaptive interval"""
        while self.running:
            try:
                had_work = await self._process_pending_tracks()
                
                # Trigger album assembly periodically after enrichments
                if self._enrichment_count >= self._album_assembly_threshold:
                    await self._assemble_albums()
                    self._enrichment_count = 0
                
                # Adaptive interval: if there was work, check again soon
                if had_work:
                    await asyncio.sleep(5)  # Quick retry if there's more to process
                else:
                    await asyncio.sleep(interval)  # Normal interval if idle
                    
            except Exception as e:
                logger.error(f"Enrichment worker error: {e}")
                await asyncio.sleep(interval)
    
    async def _process_pending_tracks(self, batch_size: int = 10) -> bool:
        """
        Process a batch of pending tracks with parallel API calls.
        Returns True if there was work to do.
        """
        async with get_session() as session:
            # Get pending tracks
            result = await session.execute(
                select(Track)
                .where(Track.enrichment_status == "pending")
                .limit(batch_size)
            )
            tracks = result.scalars().all()
            
            if not tracks:
                return False
            
            logger.info(f"Processing {len(tracks)} tracks for enrichment")
            
            # Mark all as processing first
            for track in tracks:
                track.enrichment_status = "processing"
            await session.flush()
            
            # Process in parallel (up to 5 concurrent API calls)
            async def enrich_one(track):
                try:
                    enriched = await metadata_service.enrich_track(
                        title=track.title,
                        artist=track.artist
                    )
                    
                    if enriched.get("enriched"):
                        if not track.album and enriched.get("album"):
                            track.album = enriched["album"]
                        if not track.genre and enriched.get("genre"):
                            track.genre = enriched["genre"]
                        if enriched.get("cover_url"):
                            track.cover_url = enriched["cover_url"]
                        # NO deezer_album_id - grouping by album name only
                        # Deezer IDs caused wrong album assignments
                        
                        track.enrichment_status = "completed"
                        logger.info(f"Enriched: {track.title} - {track.artist}")
                    else:
                        track.enrichment_status = "failed"
                        logger.debug(f"No data for: {track.title} - {track.artist}")
                        
                except Exception as e:
                    logger.error(f"Failed to enrich track {track.id}: {e}")
                    track.enrichment_status = "failed"
            
            # Run all enrichments concurrently
            await asyncio.gather(*[enrich_one(t) for t in tracks], return_exceptions=True)
            
            # Count successful enrichments for album assembly trigger
            self._enrichment_count += len(tracks)
            
            return True
    
    async def _assemble_albums(self):
        """Trigger album assembly for all users with enriched tracks"""
        try:
            async with get_session() as session:
                # Get distinct user IDs with completed enrichment
                from sqlalchemy import distinct
                result = await session.execute(
                    select(distinct(Track.user_id))
                    .where(
                        Track.enrichment_status == "completed",
                        Track.album.isnot(None),
                        Track.album != ""
                    )
                )
                user_ids = [row[0] for row in result.all()]
            
            for user_id in user_ids:
                try:
                    stats = await album_service.assemble_albums_for_user(user_id)
                    if stats["created"] or stats["updated"]:
                        logger.info(
                            f"Album assembly for user {user_id}: "
                            f"created={stats['created']}, updated={stats['updated']}"
                        )
                except Exception as e:
                    logger.error(f"Album assembly failed for user {user_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Album assembly error: {e}")
    
    async def get_stats(self) -> dict:
        """Get current enrichment statistics"""
        async with get_session() as session:
            result = await session.execute(
                select(
                    Track.enrichment_status,
                    func.count(Track.id)
                ).group_by(Track.enrichment_status)
            )
            
            stats = {row[0] or "pending": row[1] for row in result.all()}
            return {
                "pending": stats.get("pending", 0),
                "processing": stats.get("processing", 0),
                "completed": stats.get("completed", 0),
                "failed": stats.get("failed", 0),
                "total": sum(stats.values()),
            }
    
    async def reset_failed(self):
        """Reset failed tracks to pending for retry"""
        async with get_session() as session:
            await session.execute(
                Track.__table__.update()
                .where(Track.enrichment_status == "failed")
                .values(enrichment_status="pending")
            )
            logger.info("Reset failed tracks to pending")


# Global instance
enrichment_worker = EnrichmentWorker()

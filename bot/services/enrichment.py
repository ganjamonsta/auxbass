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

logger = logging.getLogger(__name__)


class EnrichmentWorker:
    """Background worker for metadata enrichment"""
    
    def __init__(self):
        self.running = False
        self._task: Optional[asyncio.Task] = None
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
        """Main worker loop"""
        while self.running:
            try:
                await self._process_pending_tracks()
            except Exception as e:
                logger.error(f"Enrichment worker error: {e}")
            
            await asyncio.sleep(interval)
    
    async def _process_pending_tracks(self, batch_size: int = 5):
        """Process a batch of pending tracks"""
        async with get_session() as session:
            # Get pending tracks
            result = await session.execute(
                select(Track)
                .where(Track.enrichment_status == "pending")
                .limit(batch_size)
            )
            tracks = result.scalars().all()
            
            if not tracks:
                return
            
            logger.info(f"Processing {len(tracks)} tracks for enrichment")
            
            for track in tracks:
                try:
                    # Mark as processing
                    track.enrichment_status = "processing"
                    await session.flush()
                    
                    # Enrich
                    enriched = await metadata_service.enrich_track(
                        title=track.title,
                        artist=track.artist
                    )
                    
                    if enriched.get("enriched"):
                        # Update track with new data
                        if not track.album and enriched.get("album"):
                            track.album = enriched["album"]
                        if not track.genre and enriched.get("genre"):
                            track.genre = enriched["genre"]
                        if enriched.get("cover_url"):
                            track.cover_url = enriched["cover_url"]
                        
                        track.enrichment_status = "completed"
                        logger.info(f"Enriched track: {track.title} - {track.artist}")
                    else:
                        # No data found, mark as failed
                        track.enrichment_status = "failed"
                        logger.info(f"No enrichment data for: {track.title} - {track.artist}")
                    
                except Exception as e:
                    logger.error(f"Failed to enrich track {track.id}: {e}")
                    track.enrichment_status = "failed"
    
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

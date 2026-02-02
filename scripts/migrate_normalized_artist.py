#!/usr/bin/env python3
"""
Migration script: Populate normalized_artist field for all tracks.

This enables fast SQL-based artist filtering instead of loading all tracks into Python.

Usage:
    python scripts/migrate_normalized_artist.py
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update, text
from shared.database import async_session, engine
from shared.models import Track
from shared.matching import normalize_artist

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def migrate():
    """Populate normalized_artist for all tracks."""
    
    async with async_session() as db:
        # First, add the column if it doesn't exist
        # SQLite doesn't support IF NOT EXISTS for ALTER TABLE, so we catch the error
        try:
            await db.execute(text(
                "ALTER TABLE tracks ADD COLUMN normalized_artist VARCHAR(255)"
            ))
            await db.commit()
            logger.info("Added normalized_artist column")
        except Exception as e:
            # SQLite returns "duplicate column name" error
            error_msg = str(e).lower()
            if "duplicate" in error_msg or "already exists" in error_msg:
                logger.info("Column normalized_artist already exists")
                await db.rollback()
            else:
                logger.warning(f"Column may already exist: {e}")
                await db.rollback()
        
        # Get all tracks that need updating (where normalized_artist is NULL)
        result = await db.execute(
            select(Track.id, Track.artist).where(Track.normalized_artist.is_(None))
        )
        tracks = result.all()
        
        logger.info(f"Found {len(tracks)} tracks to process")
        
        if not tracks:
            logger.info("All tracks already have normalized_artist set")
            return
        
        # Update in batches
        batch_size = 500
        updated = 0
        
        for i in range(0, len(tracks), batch_size):
            batch = tracks[i:i + batch_size]
            
            for track_id, artist in batch:
                normalized = normalize_artist(artist) if artist else None
                if normalized:
                    await db.execute(
                        update(Track)
                        .where(Track.id == track_id)
                        .values(normalized_artist=normalized)
                    )
                    updated += 1
            
            await db.commit()
            logger.info(f"Processed {min(i + batch_size, len(tracks))}/{len(tracks)} tracks")
        
        logger.info(f"Migration complete! Updated {updated} tracks with normalized_artist")
        
        # Create index if not exists (works in SQLite)
        try:
            await db.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_tracks_normalized_artist ON tracks(normalized_artist)"
            ))
            await db.commit()
            logger.info("Created index idx_tracks_normalized_artist")
        except Exception as e:
            logger.warning(f"Index may already exist: {e}")


if __name__ == "__main__":
    asyncio.run(migrate())

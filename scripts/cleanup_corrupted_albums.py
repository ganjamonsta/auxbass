"""
TG Player - Database Maintenance Script

Cleans up corrupted albums and resets tracks with bad enrichment:
- Albums where deezer_album_id artist does not match Album.artist
- Empty or corrupted albums
- Resets enrichment_status of affected tracks to PENDING
"""
import asyncio
import json
import logging
import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func, delete
from shared.database import get_session
from shared.models import Track, TrackEnrichment, Album, AlbumTrack, EnrichmentStatus
from shared.matching import normalize_artist, fuzzy_match_artist, ARTIST_MATCH_THRESHOLD

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def cleanup_corrupted_albums(dry_run: bool = False):
    """
    Find and remove corrupted albums and reset affected tracks.
    """
    logger.info(f"Starting album cleanup (dry_run={dry_run})...")
    
    try:
        async with get_session() as session:
            # 1. Check all albums
            result = await session.execute(select(Album))
            albums = list(result.scalars().all())
            
            corrupted_album_ids = []
            
            for album in albums:
                # Check full_tracklist artist consistency if present
                if album.full_tracklist:
                    try:
                        tracklist = json.loads(album.full_tracklist)
                        if tracklist and isinstance(tracklist, list):
                            # Count how many tracks have artists completely different from album.artist
                            mismatched_artists = 0
                            for t in tracklist:
                                t_artist = t.get("artist", "")
                                if t_artist and album.artist:
                                    if fuzzy_match_artist(album.artist, t_artist) < ARTIST_MATCH_THRESHOLD:
                                        mismatched_artists += 1
                            
                            # If more than half the tracklist has completely different artist, it's corrupted
                            if len(tracklist) > 0 and mismatched_artists / len(tracklist) > 0.5:
                                logger.warning(
                                    f"Corrupted album detected [ID {album.id}]: '{album.name}' by '{album.artist}' "
                                    f"has {mismatched_artists}/{len(tracklist)} tracks with mismatched artists."
                                )
                                corrupted_album_ids.append(album.id)
                    except Exception as e:
                        logger.warning(f"Failed to parse tracklist for album {album.id}: {e}")
            
            # 2. Check for empty albums
            empty_albums_result = await session.execute(
                select(Album.id)
                .outerjoin(AlbumTrack, AlbumTrack.album_id == Album.id)
                .group_by(Album.id)
                .having(func.count(AlbumTrack.id) == 0)
            )
            empty_album_ids = [row[0] for row in empty_albums_result.all()]
            
            all_bad_album_ids = list(set(corrupted_album_ids + empty_album_ids))
            logger.info(f"Found {len(all_bad_album_ids)} bad/corrupted albums (corrupted={len(corrupted_album_ids)}, empty={len(empty_album_ids)}).")
            
            if not all_bad_album_ids:
                logger.info("No corrupted albums found in database. All clean!")
                return
            
            if dry_run:
                logger.info(f"[DRY RUN] Would delete album IDs: {all_bad_album_ids}")
                return
            
            # 3. For corrupted albums with tracks: get associated track IDs to reset enrichment
            tracks_to_reset = []
            if corrupted_album_ids:
                tracks_res = await session.execute(
                    select(AlbumTrack.track_id)
                    .where(AlbumTrack.album_id.in_(corrupted_album_ids))
                )
                tracks_to_reset = list(set(row[0] for row in tracks_res.all()))
                
                logger.info(f"Unlinking and resetting {len(tracks_to_reset)} tracks...")
                
                # Delete AlbumTracks
                await session.execute(
                    delete(AlbumTrack).where(AlbumTrack.album_id.in_(corrupted_album_ids))
                )
                
                # Reset tracks to PENDING and clear corrupt enrichment
                for tid in tracks_to_reset:
                    track = await session.get(Track, tid)
                    if track:
                        track.enrichment_status = EnrichmentStatus.PENDING
                    
                    enrichment = await session.scalar(
                        select(TrackEnrichment).where(TrackEnrichment.track_id == tid)
                    )
                    if enrichment:
                        enrichment.album_name = None
                        enrichment.deezer_album_id = None
                        enrichment.track_number = None
            
            # 4. Delete bad albums
            await session.execute(
                delete(Album).where(Album.id.in_(all_bad_album_ids))
            )
            await session.commit()
            
            logger.info(
                f"Successfully cleaned up {len(all_bad_album_ids)} albums and queued "
                f"{len(tracks_to_reset)} tracks for re-enrichment!"
            )
    except Exception as e:
        logger.error(f"Database error during cleanup: {e}")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    asyncio.run(cleanup_corrupted_albums(dry_run=dry_run))

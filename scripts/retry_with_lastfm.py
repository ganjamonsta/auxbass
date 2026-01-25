#!/usr/bin/env python3
"""
Script to retry enrichment for failed tracks using Deezer + Last.fm fallback.
Run from /opt/tg_player: python scripts/retry_with_lastfm.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from shared.database import get_session
from shared.models import Track
from bot.services.metadata import MetadataService


async def main():
    # Get failed AND pending tracks (pending = reset by fix_album_field.py)
    async with get_session() as session:
        result = await session.execute(
            select(Track)
            .where(Track.enrichment_status.in_(["failed", "pending"]))
            .order_by(Track.created_at.desc())
        )
        tracks = result.scalars().all()
    
    if not tracks:
        print("No failed/pending tracks to retry")
        return
    
    print(f"Found {len(tracks)} tracks to retry (using Deezer + Last.fm)")
    print("=" * 60)
    
    service = MetadataService()
    success_count = 0
    deezer_count = 0
    lastfm_count = 0
    
    for track in tracks:
        try:
            result = await service.enrich_track(track.title, track.artist)
            
            if result.get("enriched"):
                # Update track in database
                async with get_session() as session:
                    db_track = await session.get(Track, track.id)
                    if db_track:
                        if result.get("album"):
                            db_track.album = result.get("album")
                        if result.get("genre"):
                            db_track.genre = result.get("genre")
                        if result.get("cover_url"):
                            db_track.cover_url = result.get("cover_url")
                        if result.get("album_id"):
                            db_track.deezer_album_id = result.get("album_id")
                        if result.get("deezer_id"):
                            db_track.deezer_id = result.get("deezer_id")
                        
                        db_track.enrichment_status = "success"
                        await session.commit()
                
                success_count += 1
                source = result.get("source", "unknown")
                if source == "deezer":
                    deezer_count += 1
                elif source == "lastfm":
                    lastfm_count += 1
                    
                print(f"✓ [{source}] {track.artist} - {track.title} -> {result.get('album')}")
            else:
                print(f"✗ Still failed: {track.artist} - {track.title}")
                
        except Exception as e:
            print(f"✗ Error: {track.artist} - {track.title}: {e}")
    
    await service.close()
    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total tracks: {len(tracks)}")
    print(f"Successfully enriched: {success_count}")
    print(f"  - From Deezer: {deezer_count}")
    print(f"  - From Last.fm: {lastfm_count}")
    print(f"Still failed: {len(tracks) - success_count}")


if __name__ == "__main__":
    asyncio.run(main())

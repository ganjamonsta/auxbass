#!/usr/bin/env python3
"""
Backfill full_tracklist for existing albums with deezer_album_id.

This script fetches the complete tracklist from Deezer for albums
that have a deezer_album_id but no full_tracklist.
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from shared.database import get_session
from shared.models import Album
from bot.services.enrichment.deezer import deezer_client


async def fetch_and_update_tracklist(album_id: int, deezer_album_id: int) -> bool:
    """Fetch tracklist from Deezer and update album."""
    try:
        tracks = await deezer_client.get_album_tracks(deezer_album_id)
        if not tracks:
            return False
        
        tracklist = []
        for i, t in enumerate(tracks, 1):
            tracklist.append({
                "track_number": i,
                "title": t.get("title", ""),
                "artist": t.get("artist", {}).get("name", ""),
                "duration": t.get("duration", 0),
                "deezer_id": t.get("id"),
            })
        
        async with get_session() as session:
            await session.execute(
                update(Album)
                .where(Album.id == album_id)
                .values(
                    full_tracklist=json.dumps(tracklist),
                    total_tracks=len(tracklist)
                )
            )
            await session.commit()
        
        return True
        
    except Exception as e:
        print(f"  Error for album {album_id}: {e}")
        return False


async def main():
    print("=" * 60)
    print("Backfilling album tracklists from Deezer")
    print("=" * 60)
    
    # Get albums that need tracklist
    async with get_session() as session:
        result = await session.execute(
            select(Album)
            .where(
                Album.deezer_album_id.isnot(None),
                Album.full_tracklist.is_(None)
            )
        )
        albums = result.scalars().all()
    
    print(f"\nFound {len(albums)} albums to process\n")
    
    success = 0
    failed = 0
    
    for i, album in enumerate(albums, 1):
        print(f"[{i}/{len(albums)}] {album.name} by {album.artist}...", end=" ")
        
        if await fetch_and_update_tracklist(album.id, album.deezer_album_id):
            print("✓")
            success += 1
        else:
            print("✗")
            failed += 1
        
        # Rate limiting
        await asyncio.sleep(0.2)
    
    print("\n" + "=" * 60)
    print(f"Done! Success: {success}, Failed: {failed}")
    print("=" * 60)
    
    await deezer_client.close()


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Update release dates for albums that don't have them (Last.fm albums).
Fetches release dates from Last.fm album.getInfo API.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, and_
from shared.database import get_session
from shared.models import Playlist
from bot.services.metadata import metadata_service
from shared.config import get_settings


async def update_release_dates():
    settings = get_settings()
    
    if not settings.lastfm_api_key:
        print("ERROR: LASTFM_API_KEY not set!")
        return
    
    async with get_session() as session:
        # Find auto-album playlists without release_date
        result = await session.execute(
            select(Playlist)
            .where(
                and_(
                    Playlist.is_auto_album == True,
                    Playlist.release_date.is_(None),
                    Playlist.name.isnot(None),
                    Playlist.album_artist.isnot(None)
                )
            )
        )
        playlists = result.scalars().all()
        
        print(f"Found {len(playlists)} albums without release date")
        
        updated = 0
        failed = 0
        http_session = await metadata_service._get_session()
        
        for pl in playlists:
            print(f"  Checking: {pl.album_artist} - {pl.name}...", end=" ")
            
            try:
                release_date = await metadata_service._get_lastfm_album_release_date(
                    pl.album_artist, pl.name, settings.lastfm_api_key, http_session
                )
                
                if release_date:
                    pl.release_date = release_date
                    updated += 1
                    print(f"✓ {release_date}")
                else:
                    failed += 1
                    print("✗ not found")
                    
            except Exception as e:
                failed += 1
                print(f"✗ error: {e}")
            
            # Rate limiting
            await asyncio.sleep(0.3)
        
        await session.commit()
        
        print(f"\n=== Summary ===")
        print(f"Updated: {updated}")
        print(f"Not found: {failed}")


if __name__ == "__main__":
    asyncio.run(update_release_dates())

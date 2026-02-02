#!/usr/bin/env python3
"""
Fix artists with '/' in their names.

After recent updates that added tracks where artists appear as participants,
some tracks got saved with concatenated artist names like "Ecco2k/Bladee" or "Bladee/Ecco2k".
This breaks the API routing since '/' is used as a path separator.

This script:
1. Finds all tracks/albums with '/' in artist names
2. Splits them properly (takes the first artist before '/')
3. Updates the database
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import async_session
from shared.models import Track, Album


async def fix_slash_artists():
    """Find and fix artists with '/' in their names."""
    
    async with async_session() as session:
        # Find tracks with '/' in artist names
        tracks_query = select(Track).where(Track.artist.like('%/%'))
        result = await session.execute(tracks_query)
        tracks = result.scalars().all()
        
        print(f"Found {len(tracks)} tracks with '/' in artist name:")
        
        track_updates = []
        for track in tracks:
            # Take the first artist (before the slash)
            fixed_artist = track.artist.split('/')[0].strip()
            track_updates.append({
                'id': track.id,
                'old': track.artist,
                'new': fixed_artist
            })
            print(f"  Track #{track.id}: '{track.artist}' -> '{fixed_artist}'")
            print(f"    Title: {track.title}")
        
        # Find albums with '/' in artist names
        albums_query = select(Album).where(Album.artist.like('%/%'))
        result = await session.execute(albums_query)
        albums = result.scalars().all()
        
        print(f"\nFound {len(albums)} albums with '/' in artist name:")
        
        album_updates = []
        for album in albums:
            # Take the first artist (before the slash)
            fixed_artist = album.artist.split('/')[0].strip()
            album_updates.append({
                'id': album.id,
                'old': album.artist,
                'new': fixed_artist
            })
            print(f"  Album #{album.id}: '{album.artist}' -> '{fixed_artist}'")
            print(f"    Name: {album.name}")
        
        # Ask for confirmation
        if track_updates or album_updates:
            print(f"\n{'='*60}")
            print(f"Total: {len(track_updates)} tracks, {len(album_updates)} albums to fix")
            response = input("\nProceed with updates? (yes/no): ")
            
            if response.lower() in ['yes', 'y']:
                # Update tracks
                for item in track_updates:
                    await session.execute(
                        update(Track)
                        .where(Track.id == item['id'])
                        .values(artist=item['new'])
                    )
                
                # Update albums
                for item in album_updates:
                    await session.execute(
                        update(Album)
                        .where(Album.id == item['id'])
                        .values(artist=item['new'])
                    )
                
                await session.commit()
                print(f"\n✓ Updated {len(track_updates)} tracks and {len(album_updates)} albums")
            else:
                print("Cancelled.")
        else:
            print("\nNo artists with '/' found. Database is clean!")


if __name__ == "__main__":
    asyncio.run(fix_slash_artists())

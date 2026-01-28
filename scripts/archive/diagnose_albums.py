#!/usr/bin/env python3
"""
Diagnose incorrect album assignments.
Finds tracks where the album doesn't match what's expected for that artist.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from shared.database import get_session
from shared.models import Track, UserLibrary, Playlist, PlaylistTrack


async def diagnose():
    """Find suspicious album assignments."""
    
    async with get_session() as session:
        # Find all tracks with "EXETER" album
        print("\n=== Tracks in 'EXETER' album ===")
        result = await session.execute(
            select(Track)
            .where(func.lower(Track.album) == "exeter")
        )
        exeter_tracks = result.scalars().all()
        
        for t in exeter_tracks:
            print(f"  ID={t.id}: '{t.title}' by '{t.artist}' | deezer_album_id={t.deezer_album_id}")
        
        # Find "D.O.A" tracks
        print("\n=== Tracks with 'D.O.A' in title ===")
        result = await session.execute(
            select(Track)
            .where(Track.title.ilike("%D.O.A%"))
        )
        doa_tracks = result.scalars().all()
        
        for t in doa_tracks:
            print(f"  ID={t.id}: '{t.title}' by '{t.artist}' | album='{t.album}' | deezer_album_id={t.deezer_album_id}")
        
        # Find "Rolling 200 Deep" album
        print("\n=== Tracks in 'Rolling 200 Deep' album ===")
        result = await session.execute(
            select(Track)
            .where(func.lower(Track.album).contains("rolling"))
        )
        rolling_tracks = result.scalars().all()
        
        for t in rolling_tracks:
            print(f"  ID={t.id}: '{t.title}' by '{t.artist}' | album='{t.album}' | deezer_album_id={t.deezer_album_id}")
        
        # Find "BE NICE TO ME" tracks
        print("\n=== Tracks with 'BE NICE TO ME' in title ===")
        result = await session.execute(
            select(Track)
            .where(Track.title.ilike("%BE NICE TO ME%"))
        )
        benice_tracks = result.scalars().all()
        
        for t in benice_tracks:
            print(f"  ID={t.id}: '{t.title}' by '{t.artist}' | album='{t.album}' | deezer_album_id={t.deezer_album_id}")
        
        # Find playlists for these albums
        print("\n=== Auto-album playlists ===")
        result = await session.execute(
            select(Playlist)
            .where(Playlist.is_auto_album == True)
            .where(
                (func.lower(Playlist.name) == "exeter") |
                (func.lower(Playlist.name).contains("rolling")) |
                (func.lower(Playlist.name).contains("cold visions"))
            )
        )
        playlists = result.scalars().all()
        
        for pl in playlists:
            # Count tracks
            count = await session.scalar(
                select(func.count(PlaylistTrack.id))
                .where(PlaylistTrack.playlist_id == pl.id)
            )
            print(f"  Playlist ID={pl.id}: '{pl.name}' by '{pl.album_artist}' | "
                  f"deezer_album_id={pl.deezer_album_id} | tracks={count}")


if __name__ == "__main__":
    print("Album Diagnosis Script")
    print("="*50)
    asyncio.run(diagnose())

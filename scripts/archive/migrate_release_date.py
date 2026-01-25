#!/usr/bin/env python3
"""
Migration script to add release_date column to playlists and tracks tables
and populate it from Deezer API for existing auto-albums and tracks
"""
import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from shared.database import engine, get_session
from shared.models import Playlist, Track
from sqlalchemy import select


async def add_columns():
    """Add release_date column to playlists and tracks tables if they don't exist"""
    async with engine.begin() as conn:
        # Add to playlists table
        try:
            await conn.execute(text("""
                ALTER TABLE playlists 
                ADD COLUMN IF NOT EXISTS release_date VARCHAR(20)
            """))
            print("✅ playlists.release_date column ready")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("✅ playlists.release_date already exists")
            else:
                print(f"⚠️  playlists: {e}")
        
        # Add to tracks table
        try:
            await conn.execute(text("""
                ALTER TABLE tracks 
                ADD COLUMN IF NOT EXISTS release_date VARCHAR(20)
            """))
            print("✅ tracks.release_date column ready")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("✅ tracks.release_date already exists")
            else:
                print(f"⚠️  tracks: {e}")


async def populate_release_dates():
    """Populate release_date from Deezer for albums with deezer_album_id"""
    from bot.services.metadata import metadata_service
    
    async with get_session() as session:
        # First, let's see stats
        total_result = await session.execute(
            select(Playlist).where(Playlist.is_auto_album == True)
        )
        all_albums = total_result.scalars().all()
        print(f"Total auto-albums: {len(all_albums)}")
        
        with_deezer_id = [a for a in all_albums if a.deezer_album_id]
        print(f"Albums with deezer_album_id: {len(with_deezer_id)}")
        
        without_deezer_id = [a for a in all_albums if not a.deezer_album_id]
        print(f"Albums WITHOUT deezer_album_id: {len(without_deezer_id)}")
        
        # Get all auto-albums with deezer_album_id but no release_date
        result = await session.execute(
            select(Playlist)
            .where(Playlist.is_auto_album == True)
            .where(Playlist.deezer_album_id.isnot(None))
            .where(Playlist.release_date.is_(None))
        )
        albums = result.scalars().all()
        
        print(f"\nAlbums to update (have deezer_id, no release_date): {len(albums)}")
        
        updated = 0
        for album in albums:
            try:
                release_date = await metadata_service.get_album_release_date(album.deezer_album_id)
                if release_date:
                    album.release_date = release_date
                    updated += 1
                    print(f"  Updated: {album.name} -> {release_date}")
            except Exception as e:
                print(f"  Error for {album.name}: {e}")
        
        await session.commit()
        print(f"\nUpdated {updated} albums with release dates")
        
        # Now try to find deezer_album_id for albums that don't have it
        print(f"\n--- Searching Deezer for {len(without_deezer_id)} albums without deezer_id ---")
        
        found = 0
        for album in without_deezer_id:
            try:
                # Search by album name and artist
                artist = album.album_artist or ""
                search_result = await metadata_service.search_deezer_album(album.name, artist)
                
                if search_result:
                    album.deezer_album_id = search_result.get("album_id")
                    album.release_date = search_result.get("release_date")
                    if not album.cover_url and search_result.get("cover_url"):
                        album.cover_url = search_result.get("cover_url")
                    found += 1
                    print(f"  Found: {album.name} by {artist} -> {search_result.get('release_date')}")
            except Exception as e:
                print(f"  Error searching {album.name}: {e}")
        
        await session.commit()
        print(f"\nFound and updated {found} additional albums from Deezer search")
    
    await metadata_service.close()


async def populate_track_release_dates():
    """Populate release_date for tracks with deezer_album_id"""
    from bot.services.metadata import metadata_service
    
    async with get_session() as session:
        # Get tracks with deezer_album_id but no release_date
        result = await session.execute(
            select(Track)
            .where(Track.deezer_album_id.isnot(None))
            .where(Track.release_date.is_(None))
        )
        tracks = list(result.scalars().all())
        
        print(f"\n📀 Tracks with deezer_album_id but no release_date: {len(tracks)}")
        
        # Group by deezer_album_id to avoid duplicate API calls
        album_dates = {}
        updated = 0
        
        for track in tracks:
            album_id = track.deezer_album_id
            
            # Check cache first
            if album_id in album_dates:
                release_date = album_dates[album_id]
            else:
                try:
                    release_date = await metadata_service.get_album_release_date(album_id)
                    album_dates[album_id] = release_date
                except Exception as e:
                    print(f"  ❌ Error getting date for album {album_id}: {e}")
                    album_dates[album_id] = None
                    continue
            
            if release_date:
                track.release_date = release_date
                updated += 1
                print(f"  ✅ {track.artist} - {track.title} -> {release_date}")
        
        await session.commit()
        print(f"\n✨ Updated {updated} tracks with release dates")
    
    await metadata_service.close()


async def main():
    print("=" * 50)
    print("Migration: Add release_date to playlists & tracks")
    print("=" * 50)
    
    await add_columns()
    
    print("\n📅 Populating playlist release dates from Deezer...")
    await populate_release_dates()
    
    print("\n📀 Populating track release dates from Deezer...")
    await populate_track_release_dates()
    
    print("\n✨ Migration complete!")


if __name__ == "__main__":
    asyncio.run(main())

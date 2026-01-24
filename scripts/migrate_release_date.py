#!/usr/bin/env python3
"""
Migration script to add release_date column to playlists table
and populate it from Deezer API for existing auto-albums
"""
import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from shared.database import engine, get_session
from shared.models import Playlist
from sqlalchemy import select


async def add_column():
    """Add release_date column if it doesn't exist"""
    async with engine.begin() as conn:
        # Check if column exists using SQLite's PRAGMA (works for SQLite)
        # For PostgreSQL, use information_schema
        try:
            result = await conn.execute(text("PRAGMA table_info(playlists)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "release_date" not in columns:
                print("Adding release_date column to playlists table...")
                await conn.execute(text("""
                    ALTER TABLE playlists 
                    ADD COLUMN release_date VARCHAR(20)
                """))
                print("Column added successfully!")
            else:
                print("Column release_date already exists")
        except Exception as e:
            # Fallback: try to add column, ignore if it exists
            print(f"Checking column existence failed ({e}), trying to add...")
            try:
                await conn.execute(text("""
                    ALTER TABLE playlists 
                    ADD COLUMN release_date VARCHAR(20)
                """))
                print("Column added successfully!")
            except Exception as e2:
                if "duplicate column" in str(e2).lower() or "already exists" in str(e2).lower():
                    print("Column release_date already exists")
                else:
                    raise


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


async def main():
    print("=" * 50)
    print("Migration: Add release_date to playlists")
    print("=" * 50)
    
    await add_column()
    
    print("\nPopulating release dates from Deezer...")
    await populate_release_dates()
    
    print("\nMigration complete!")


if __name__ == "__main__":
    asyncio.run(main())

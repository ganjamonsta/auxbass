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
        # Check if column exists
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'playlists' AND column_name = 'release_date'
        """))
        
        if result.fetchone() is None:
            print("Adding release_date column to playlists table...")
            await conn.execute(text("""
                ALTER TABLE playlists 
                ADD COLUMN release_date VARCHAR(20)
            """))
            print("Column added successfully!")
        else:
            print("Column release_date already exists")


async def populate_release_dates():
    """Populate release_date from Deezer for albums with deezer_album_id"""
    from bot.services.metadata import metadata_service
    
    async with get_session() as session:
        # Get all auto-albums with deezer_album_id but no release_date
        result = await session.execute(
            select(Playlist)
            .where(Playlist.is_auto_album == True)
            .where(Playlist.deezer_album_id.isnot(None))
            .where(Playlist.release_date.is_(None))
        )
        albums = result.scalars().all()
        
        print(f"Found {len(albums)} albums to update")
        
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
        print(f"Updated {updated} albums with release dates")
    
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

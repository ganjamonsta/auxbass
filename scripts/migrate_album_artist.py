"""
Migration script to add album_artist column and split existing album names.
Existing album names like "Artist — Album" will be split into:
- name = "Album" 
- album_artist = "Artist"
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.database import get_session, engine
from shared.models import Playlist
from sqlalchemy import select, text


async def migrate():
    """Add album_artist column and migrate existing data"""
    
    # First, add the column if it doesn't exist
    async with engine.begin() as conn:
        # Check if column exists
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'playlists' AND column_name = 'album_artist'
        """))
        
        if not result.fetchone():
            print("Adding album_artist column to playlists table...")
            await conn.execute(text("""
                ALTER TABLE playlists 
                ADD COLUMN album_artist VARCHAR(255)
            """))
            print("Column added successfully!")
        else:
            print("Column album_artist already exists")
    
    # Now migrate existing album playlists
    async with get_session() as session:
        result = await session.execute(
            select(Playlist).where(
                Playlist.is_auto_album == True,
                Playlist.album_artist.is_(None)
            )
        )
        playlists = result.scalars().all()
        
        print(f"Found {len(playlists)} album playlists to migrate")
        
        for playlist in playlists:
            # Split "Artist — Album" format
            if " — " in playlist.name:
                parts = playlist.name.split(" — ", 1)
                artist = parts[0].strip()
                album = parts[1].strip() if len(parts) > 1 else playlist.name
                
                playlist.album_artist = artist
                playlist.name = album
                print(f"  Migrated: '{artist}' — '{album}'")
            else:
                # No separator, try to get artist from tracks
                print(f"  Skipped (no separator): {playlist.name}")
        
        await session.commit()
        print(f"Migration complete!")


if __name__ == "__main__":
    asyncio.run(migrate())

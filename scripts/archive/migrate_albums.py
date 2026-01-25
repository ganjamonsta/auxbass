"""
Migration script to add album assembly related columns
- tracks.deezer_album_id
- playlists.is_auto_album
- playlists.deezer_album_id
- playlists.cover_url
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from shared.database import engine


async def migrate():
    """Add new columns for auto-album assembly"""
    
    async with engine.begin() as conn:
        # Check if using SQLite or PostgreSQL
        try:
            # SQLite
            result = await conn.execute(text("PRAGMA table_info(tracks)"))
            columns = {row[1] for row in result.fetchall()}
            is_sqlite = True
        except:
            # PostgreSQL
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'tracks'
            """))
            columns = {row[0] for row in result.fetchall()}
            is_sqlite = False
        
        print(f"Database type: {'SQLite' if is_sqlite else 'PostgreSQL'}")
        print(f"Existing track columns: {columns}")
        
        # Add deezer_album_id to tracks
        if 'deezer_album_id' not in columns:
            print("Adding deezer_album_id column to tracks...")
            await conn.execute(text(
                "ALTER TABLE tracks ADD COLUMN deezer_album_id INTEGER"
            ))
            print("✓ tracks.deezer_album_id added")
        else:
            print("✓ tracks.deezer_album_id already exists")
        
        # Check playlists columns
        if is_sqlite:
            result = await conn.execute(text("PRAGMA table_info(playlists)"))
            playlist_columns = {row[1] for row in result.fetchall()}
        else:
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'playlists'
            """))
            playlist_columns = {row[0] for row in result.fetchall()}
        
        print(f"Existing playlist columns: {playlist_columns}")
        
        # Add is_auto_album to playlists
        if 'is_auto_album' not in playlist_columns:
            print("Adding is_auto_album column to playlists...")
            await conn.execute(text(
                "ALTER TABLE playlists ADD COLUMN is_auto_album BOOLEAN DEFAULT FALSE"
            ))
            print("✓ playlists.is_auto_album added")
        else:
            print("✓ playlists.is_auto_album already exists")
        
        # Add deezer_album_id to playlists
        if 'deezer_album_id' not in playlist_columns:
            print("Adding deezer_album_id column to playlists...")
            await conn.execute(text(
                "ALTER TABLE playlists ADD COLUMN deezer_album_id INTEGER"
            ))
            print("✓ playlists.deezer_album_id added")
        else:
            print("✓ playlists.deezer_album_id already exists")
        
        # Add cover_url to playlists
        if 'cover_url' not in playlist_columns:
            print("Adding cover_url column to playlists...")
            await conn.execute(text(
                "ALTER TABLE playlists ADD COLUMN cover_url VARCHAR(500)"
            ))
            print("✓ playlists.cover_url added")
        else:
            print("✓ playlists.cover_url already exists")
        
        # Add index for deezer_album_id on tracks
        print("Adding index for tracks.deezer_album_id...")
        try:
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_tracks_deezer_album_id ON tracks(deezer_album_id)"
            ))
            print("✓ Index added")
        except Exception as e:
            print(f"⚠ Index may already exist: {e}")
    
    print("\n✅ Migration complete!")


if __name__ == "__main__":
    asyncio.run(migrate())

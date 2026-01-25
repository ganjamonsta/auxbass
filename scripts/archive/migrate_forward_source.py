"""
Migration: Add forward source tracking and auto-playlists
Adds forward_from fields to tracks and is_auto_source flag to playlists
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.database import engine
from sqlalchemy import text


async def column_exists(conn, table: str, column: str) -> bool:
    """Check if a column exists in SQLite table"""
    result = await conn.execute(text(f"PRAGMA table_info({table})"))
    columns = [row[1] for row in result.fetchall()]
    return column in columns


async def index_exists(conn, index_name: str) -> bool:
    """Check if an index exists in SQLite"""
    result = await conn.execute(text(
        f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index_name}'"
    ))
    return result.fetchone() is not None


async def migrate():
    """Add forward source fields to tracks and playlists"""
    
    async with engine.begin() as conn:
        # Add forward source fields to tracks
        track_columns = [
            ("forward_from_id", "BIGINT"),
            ("forward_from_username", "VARCHAR(255)"),
            ("forward_from_name", "VARCHAR(255)"),
            ("forward_from_type", "VARCHAR(20)"),
        ]
        
        for col_name, col_type in track_columns:
            if not await column_exists(conn, "tracks", col_name):
                try:
                    await conn.execute(text(f"ALTER TABLE tracks ADD COLUMN {col_name} {col_type}"))
                    print(f"✅ Added column tracks.{col_name}")
                except Exception as e:
                    print(f"⚠️ tracks.{col_name}: {e}")
            else:
                print(f"⏭️ Column tracks.{col_name} already exists")
        
        # Add auto-source playlist fields
        playlist_columns = [
            ("is_auto_source", "BOOLEAN DEFAULT FALSE"),
            ("source_id", "BIGINT"),
            ("source_type", "VARCHAR(20)"),
        ]
        
        for col_name, col_type in playlist_columns:
            if not await column_exists(conn, "playlists", col_name):
                try:
                    await conn.execute(text(f"ALTER TABLE playlists ADD COLUMN {col_name} {col_type}"))
                    print(f"✅ Added column playlists.{col_name}")
                except Exception as e:
                    print(f"⚠️ playlists.{col_name}: {e}")
            else:
                print(f"⏭️ Column playlists.{col_name} already exists")
        
        # Create indexes (SQLite supports IF NOT EXISTS for indexes)
        indexes = [
            ("idx_tracks_forward_from_id", "CREATE INDEX IF NOT EXISTS idx_tracks_forward_from_id ON tracks(forward_from_id)"),
            ("idx_playlists_auto_source", "CREATE INDEX IF NOT EXISTS idx_playlists_auto_source ON playlists(user_id, is_auto_source, source_id)"),
        ]
        
        for idx_name, sql in indexes:
            try:
                await conn.execute(text(sql))
                print(f"✅ Index {idx_name} ready")
            except Exception as e:
                print(f"⚠️ Index {idx_name}: {e}")
        
        print("\n✅ Migration completed!")


if __name__ == "__main__":
    asyncio.run(migrate())

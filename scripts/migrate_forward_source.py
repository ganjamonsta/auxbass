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


async def migrate():
    """Add forward source fields to tracks and playlists"""
    
    async with engine.begin() as conn:
        # Add forward source fields to tracks
        migrations = [
            # Forward source info for tracks
            """
            ALTER TABLE tracks 
            ADD COLUMN IF NOT EXISTS forward_from_id BIGINT,
            ADD COLUMN IF NOT EXISTS forward_from_username VARCHAR(255),
            ADD COLUMN IF NOT EXISTS forward_from_name VARCHAR(255),
            ADD COLUMN IF NOT EXISTS forward_from_type VARCHAR(20)
            """,
            
            # Auto-source playlist flag
            """
            ALTER TABLE playlists 
            ADD COLUMN IF NOT EXISTS is_auto_source BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS source_id BIGINT,
            ADD COLUMN IF NOT EXISTS source_type VARCHAR(20)
            """,
            
            # Index for faster lookup by source
            """
            CREATE INDEX IF NOT EXISTS idx_tracks_forward_from_id 
            ON tracks(forward_from_id) WHERE forward_from_id IS NOT NULL
            """,
            
            # Index for auto-source playlists
            """
            CREATE INDEX IF NOT EXISTS idx_playlists_auto_source 
            ON playlists(user_id, is_auto_source, source_id) 
            WHERE is_auto_source = TRUE
            """,
        ]
        
        for sql in migrations:
            try:
                await conn.execute(text(sql))
                print(f"✅ Executed: {sql[:60]}...")
            except Exception as e:
                print(f"⚠️ {e}")
        
        print("\n✅ Migration completed!")


if __name__ == "__main__":
    asyncio.run(migrate())

"""
Database migration script for TG Player
Adds new fields to tracks table
"""
import asyncio
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from shared.database import engine


async def migrate():
    """Run database migrations"""
    print("Running migrations...")
    
    async with engine.begin() as conn:
        # Check if columns exist
        result = await conn.execute(text("PRAGMA table_info(tracks)"))
        columns = [row[1] for row in result.fetchall()]
        
        # Add play_count if not exists
        if 'play_count' not in columns:
            print("Adding play_count column...")
            await conn.execute(text(
                "ALTER TABLE tracks ADD COLUMN play_count INTEGER DEFAULT 0"
            ))
            print("✓ play_count column added")
        else:
            print("• play_count column already exists")
        
        # Add last_played_at if not exists
        if 'last_played_at' not in columns:
            print("Adding last_played_at column...")
            await conn.execute(text(
                "ALTER TABLE tracks ADD COLUMN last_played_at DATETIME"
            ))
            print("✓ last_played_at column added")
        else:
            print("• last_played_at column already exists")
        
        # Add is_liked if not exists
        if 'is_liked' not in columns:
            print("Adding is_liked column...")
            await conn.execute(text(
                "ALTER TABLE tracks ADD COLUMN is_liked BOOLEAN DEFAULT 0"
            ))
            print("✓ is_liked column added")
        else:
            print("• is_liked column already exists")
        
        # Add liked_at if not exists
        if 'liked_at' not in columns:
            print("Adding liked_at column...")
            await conn.execute(text(
                "ALTER TABLE tracks ADD COLUMN liked_at DATETIME"
            ))
            print("✓ liked_at column added")
        else:
            print("• liked_at column already exists")
    
    print("\nMigrations completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate())

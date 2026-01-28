#!/usr/bin/env python3
"""
Migration: Add full_tracklist column to albums table.

This stores the complete album tracklist from Deezer for showing
missing tracks in the user's library.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from shared.database import engine


async def migrate():
    """Add full_tracklist column to albums table"""
    
    async with engine.begin() as conn:
        # Check if column already exists
        result = await conn.execute(text("PRAGMA table_info(albums)"))
        columns = {row[1] for row in result.fetchall()}
        
        if 'full_tracklist' not in columns:
            print("Adding full_tracklist column...")
            await conn.execute(text(
                "ALTER TABLE albums ADD COLUMN full_tracklist TEXT"
            ))
            print("✓ full_tracklist column added")
        else:
            print("✓ full_tracklist column already exists")
    
    print("\nMigration complete!")


if __name__ == "__main__":
    asyncio.run(migrate())

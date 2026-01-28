"""
Migration: Add privacy fields to users table
- hide_from_search: Hide from user search, keep library visible
- hide_profile: Hide library and albums from others
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from shared.database import engine


async def migrate():
    """Add privacy columns to users table"""
    async with engine.begin() as conn:
        # Check if columns exist first (SQLite uses PRAGMA table_info)
        result = await conn.execute(text("PRAGMA table_info(users)"))
        existing_columns = {row[1] for row in result.fetchall()}  # row[1] is column name
        
        if 'hide_from_search' not in existing_columns:
            print("Adding hide_from_search column...")
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN hide_from_search BOOLEAN DEFAULT FALSE
            """))
            print("✓ hide_from_search column added")
        else:
            print("✓ hide_from_search column already exists")
        
        if 'hide_profile' not in existing_columns:
            print("Adding hide_profile column...")
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN hide_profile BOOLEAN DEFAULT FALSE
            """))
            print("✓ hide_profile column added")
        else:
            print("✓ hide_profile column already exists")
        
        print("\n✅ Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate())

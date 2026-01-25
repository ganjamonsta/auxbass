"""
Migration script to add cover_url and enrichment_status columns to tracks table
Run this on the server after deployment
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from shared.database import engine


async def migrate():
    """Add new columns for metadata enrichment"""
    
    async with engine.begin() as conn:
        # Check existing columns
        result = await conn.execute(text("PRAGMA table_info(tracks)"))
        columns = {row[1] for row in result.fetchall()}
        
        if 'cover_url' not in columns:
            print("Adding cover_url column...")
            await conn.execute(text(
                "ALTER TABLE tracks ADD COLUMN cover_url VARCHAR(500)"
            ))
            print("✓ cover_url added")
        else:
            print("✓ cover_url already exists")
        
        if 'enrichment_status' not in columns:
            print("Adding enrichment_status column...")
            await conn.execute(text(
                "ALTER TABLE tracks ADD COLUMN enrichment_status VARCHAR(20) DEFAULT 'pending'"
            ))
            print("✓ enrichment_status added")
        else:
            print("✓ enrichment_status already exists")
    
    print("\nMigration complete!")


if __name__ == "__main__":
    asyncio.run(migrate())

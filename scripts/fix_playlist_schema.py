import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Add parent directory to path to import shared
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import get_settings

async def fix_schema():
    settings = get_settings()
    url = settings.database_url
    print(f"Connecting to database...")
    
    engine = create_async_engine(url)
    
    async with engine.begin() as conn:
        print("Checking playlists table...")
        # Check if column exists first
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='playlists' AND column_name='user_id'"
        ))
        if result.scalar():
            print("Found 'user_id' column. Renaming to 'owner_id'...")
            await conn.execute(text("ALTER TABLE playlists RENAME COLUMN user_id TO owner_id"))
            print("✅ Renamed successfully.")
        else:
            print("Column 'user_id' not found in playlists. checking for owner_id...")
            result = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='playlists' AND column_name='owner_id'"
            ))
            if result.scalar():
                print("Column 'owner_id' already exists. No action needed.")
            else:
                print("❌ Neither user_id nor owner_id found!")

if __name__ == "__main__":
    asyncio.run(fix_schema())

"""
TG Player - Database Migration for Social Features

Adds user_follows table for friend following functionality.
Run this before restarting the API.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from shared.database import engine


async def run_migration():
    """Run the migration"""
    async with engine.begin() as conn:
        # Create user_follows table (SQLite compatible)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_follows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                follower_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                following_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (follower_id, following_id)
            )
        """))
        
        # Create indexes
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_follow_follower 
            ON user_follows(follower_id)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_follow_following 
            ON user_follows(following_id)
        """))
        
        print("✅ Created user_follows table with indexes")
        
        # Check if is_public column exists in playlists
        result = await conn.execute(text("PRAGMA table_info(playlists)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'is_public' not in columns:
            await conn.execute(text("""
                ALTER TABLE playlists ADD COLUMN is_public INTEGER DEFAULT 0
            """))
            print("✅ Added is_public column to playlists")
        else:
            print("ℹ️ is_public column already exists")
        
        if 'share_code' not in columns:
            await conn.execute(text("""
                ALTER TABLE playlists ADD COLUMN share_code TEXT
            """))
            print("✅ Added share_code column to playlists")
        else:
            print("ℹ️ share_code column already exists")
    
    print("\n🎉 Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_migration())

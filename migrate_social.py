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
        # Create user_follows table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_follows (
                id SERIAL PRIMARY KEY,
                follower_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                following_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT NOW(),
                CONSTRAINT uq_user_follow UNIQUE (follower_id, following_id)
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
        
        # Ensure playlists.is_public exists (it should already)
        try:
            await conn.execute(text("""
                ALTER TABLE playlists 
                ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE
            """))
            print("✅ Ensured is_public column exists on playlists")
        except Exception as e:
            print(f"ℹ️ is_public column check: {e}")
        
        # Ensure playlists.share_code exists
        try:
            await conn.execute(text("""
                ALTER TABLE playlists 
                ADD COLUMN IF NOT EXISTS share_code VARCHAR(50) UNIQUE
            """))
            print("✅ Ensured share_code column exists on playlists")
        except Exception as e:
            print(f"ℹ️ share_code column check: {e}")
    
    print("\n🎉 Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_migration())

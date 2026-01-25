"""
Migration script: Convert to global library model

This migration:
1. Creates user_library table
2. Removes the user_id + file_unique_id constraint (now globally unique)
3. Adds is_public column to tracks
4. Migrates existing user track relationships to user_library
5. Deduplicates tracks by file_unique_id (keeps first upload)
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from shared.database import engine
from shared.config import get_settings

settings = get_settings()
is_sqlite = settings.database_url.startswith("sqlite")


async def migrate():
    """Run migration to global library model"""
    print("🚀 Starting migration to global library model...")
    print(f"   Database: {'SQLite' if is_sqlite else 'PostgreSQL'}")
    
    async with engine.begin() as conn:
        # Step 1: Create user_library table
        print("\n📦 Step 1: Creating user_library table...")
        
        if is_sqlite:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_library (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id BIGINT NOT NULL,
                    track_id INTEGER NOT NULL,
                    source VARCHAR(20) DEFAULT 'uploaded',
                    is_liked BOOLEAN DEFAULT 0,
                    liked_at DATETIME,
                    play_count INTEGER DEFAULT 0,
                    last_played_at DATETIME,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
                    UNIQUE(user_id, track_id)
                )
            """))
        else:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_library (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    track_id INTEGER NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
                    source VARCHAR(20) DEFAULT 'uploaded',
                    is_liked BOOLEAN DEFAULT FALSE,
                    liked_at TIMESTAMP,
                    play_count INTEGER DEFAULT 0,
                    last_played_at TIMESTAMP,
                    added_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user_id, track_id)
                )
            """))
        print("   ✓ user_library table created")
        
        # Step 2: Add is_public column to tracks if not exists
        print("\n📦 Step 2: Adding is_public column to tracks...")
        
        if is_sqlite:
            result = await conn.execute(text("PRAGMA table_info(tracks)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'is_public' not in columns:
                await conn.execute(text(
                    "ALTER TABLE tracks ADD COLUMN is_public BOOLEAN DEFAULT 1"
                ))
                print("   ✓ is_public column added")
            else:
                print("   • is_public column already exists")
        else:
            await conn.execute(text("""
                ALTER TABLE tracks 
                ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT TRUE
            """))
            print("   ✓ is_public column added (or already exists)")
        
        # Step 3: Migrate existing data to user_library
        print("\n📦 Step 3: Migrating existing track ownership to user_library...")
        
        # Get existing tracks with their user relationships
        result = await conn.execute(text("""
            SELECT id, user_id, is_liked, liked_at, play_count, last_played_at, created_at
            FROM tracks
        """))
        tracks = result.fetchall()
        print(f"   Found {len(tracks)} tracks to migrate")
        
        migrated = 0
        for track in tracks:
            track_id, user_id, is_liked, liked_at, play_count, last_played_at, created_at = track
            
            # Check if entry already exists
            existing = await conn.execute(text("""
                SELECT 1 FROM user_library WHERE user_id = :user_id AND track_id = :track_id
            """), {"user_id": user_id, "track_id": track_id})
            
            if not existing.fetchone():
                await conn.execute(text("""
                    INSERT INTO user_library (user_id, track_id, source, is_liked, liked_at, play_count, last_played_at, added_at)
                    VALUES (:user_id, :track_id, 'uploaded', :is_liked, :liked_at, :play_count, :last_played_at, :added_at)
                """), {
                    "user_id": user_id,
                    "track_id": track_id,
                    "is_liked": is_liked or False,
                    "liked_at": liked_at,
                    "play_count": play_count or 0,
                    "last_played_at": last_played_at,
                    "added_at": created_at,
                })
                migrated += 1
        
        print(f"   ✓ Migrated {migrated} track entries to user_library")
        
        # Step 4: Find and handle duplicates by file_unique_id
        print("\n📦 Step 4: Deduplicating tracks by file_unique_id...")
        
        result = await conn.execute(text("""
            SELECT file_unique_id, COUNT(*) as cnt
            FROM tracks
            GROUP BY file_unique_id
            HAVING COUNT(*) > 1
        """))
        duplicates = result.fetchall()
        
        if duplicates:
            print(f"   Found {len(duplicates)} duplicate groups")
            
            for file_unique_id, count in duplicates:
                # Get all tracks with this file_unique_id, ordered by created_at
                result = await conn.execute(text("""
                    SELECT id, user_id FROM tracks 
                    WHERE file_unique_id = :fuid
                    ORDER BY created_at ASC
                """), {"fuid": file_unique_id})
                dup_tracks = result.fetchall()
                
                # Keep the first one, merge others
                keeper_id = dup_tracks[0][0]
                
                for track_id, user_id in dup_tracks[1:]:
                    # Add user to library if not already there
                    existing = await conn.execute(text("""
                        SELECT 1 FROM user_library WHERE user_id = :user_id AND track_id = :keeper_id
                    """), {"user_id": user_id, "keeper_id": keeper_id})
                    
                    if not existing.fetchone():
                        # Copy their library entry to point to keeper
                        await conn.execute(text("""
                            INSERT INTO user_library (user_id, track_id, source, is_liked, liked_at, play_count, last_played_at, added_at)
                            SELECT :user_id, :keeper_id, 'uploaded', is_liked, liked_at, play_count, last_played_at, added_at
                            FROM user_library WHERE user_id = :user_id AND track_id = :track_id
                        """), {"user_id": user_id, "keeper_id": keeper_id, "track_id": track_id})
                    
                    # Update playlist_tracks to point to keeper
                    await conn.execute(text("""
                        UPDATE playlist_tracks SET track_id = :keeper_id
                        WHERE track_id = :track_id
                    """), {"keeper_id": keeper_id, "track_id": track_id})
                    
                    # Delete duplicate track's library entries
                    await conn.execute(text("""
                        DELETE FROM user_library WHERE track_id = :track_id
                    """), {"track_id": track_id})
                    
                    # Delete the duplicate track
                    await conn.execute(text("""
                        DELETE FROM tracks WHERE id = :track_id
                    """), {"track_id": track_id})
            
            print(f"   ✓ Merged duplicates, kept oldest uploads")
        else:
            print("   • No duplicates found")
        
        # Step 5: Create indexes for user_library
        print("\n📦 Step 5: Creating indexes...")
        
        if is_sqlite:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_library_user ON user_library(user_id)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_library_liked ON user_library(user_id, is_liked)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_tracks_public ON tracks(is_public)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_tracks_play_count ON tracks(play_count)
            """))
        else:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_library_user ON user_library(user_id)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_library_liked ON user_library(user_id, is_liked)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_tracks_public ON tracks(is_public)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_tracks_play_count ON tracks(play_count)
            """))
        
        print("   ✓ Indexes created")
        
        # Step 6: Update constraint (PostgreSQL only - SQLite can't alter constraints)
        if not is_sqlite:
            print("\n📦 Step 6: Updating unique constraint...")
            
            # Drop old constraint if exists
            try:
                await conn.execute(text("""
                    ALTER TABLE tracks DROP CONSTRAINT IF EXISTS uq_user_track
                """))
                print("   ✓ Dropped old uq_user_track constraint")
            except Exception as e:
                print(f"   • Old constraint doesn't exist or already dropped: {e}")
            
            # Add new unique constraint on file_unique_id only
            try:
                await conn.execute(text("""
                    ALTER TABLE tracks ADD CONSTRAINT uq_file_unique_id UNIQUE (file_unique_id)
                """))
                print("   ✓ Added new unique constraint on file_unique_id")
            except Exception as e:
                print(f"   • Constraint already exists: {e}")
        else:
            print("\n📦 Step 6: Skipping constraint update (SQLite limitations)")
            print("   Note: For SQLite, the unique constraint is defined in the model")
    
    print("\n✅ Migration completed successfully!")
    print("\n📝 Summary:")
    print("   - Created user_library table for personal track collections")
    print("   - Added is_public flag to tracks (default: true)")
    print("   - Migrated existing ownership to user_library")
    print("   - Deduplicated tracks by file_unique_id")
    print("   - Tracks are now globally unique and shareable!")


if __name__ == "__main__":
    asyncio.run(migrate())

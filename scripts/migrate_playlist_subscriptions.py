#!/usr/bin/env python3
"""
Migration script to add playlist_subscriptions table.

Allows users to subscribe to public playlists from other users.
Subscribed playlists appear in user's library and auto-update.

Run on server:
    python scripts/migrate_playlist_subscriptions.py
"""
import sqlite3
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import get_settings


def migrate():
    """Create playlist_subscriptions table if not exists."""
    settings = get_settings()
    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
    
    print(f"Connecting to database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if table already exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='playlist_subscriptions'
    """)
    
    if cursor.fetchone():
        print("Table 'playlist_subscriptions' already exists. Nothing to do.")
        conn.close()
        return
    
    print("Creating 'playlist_subscriptions' table...")
    
    # Create the table
    cursor.execute("""
        CREATE TABLE playlist_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
            subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, playlist_id)
        )
    """)
    
    # Create indexes
    cursor.execute("""
        CREATE INDEX idx_playlist_subscription_user 
        ON playlist_subscriptions(user_id)
    """)
    
    cursor.execute("""
        CREATE INDEX idx_playlist_subscription_playlist 
        ON playlist_subscriptions(playlist_id)
    """)
    
    conn.commit()
    print("Migration complete! Table 'playlist_subscriptions' created successfully.")
    
    # Verify
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='playlist_subscriptions'
    """)
    if cursor.fetchone():
        print("✓ Table verified")
    
    cursor.execute("PRAGMA table_info(playlist_subscriptions)")
    columns = cursor.fetchall()
    print(f"Columns: {[col[1] for col in columns]}")
    
    conn.close()


if __name__ == "__main__":
    migrate()

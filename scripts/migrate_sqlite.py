"""
Automatic SQLite Schema Migration for TG Player
Adds all missing columns to existing SQLite database tables safely.
"""
import sqlite3
import os
import sys

def migrate_sqlite_db(db_path: str):
    if not os.path.exists(db_path):
        print(f"[!] Database file {db_path} does not exist. Nothing to migrate.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Define all required columns per table with their SQLite types & defaults
    schema_definitions = {
        "channel_messages": [
            ("status", "TEXT DEFAULT 'sent'"),
            ("retry_count", "INTEGER DEFAULT 0"),
            ("last_error", "TEXT"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ],
        "tracks": [
            ("file_name", "TEXT"),
            ("normalized_artist", "TEXT"),
            ("is_public", "INTEGER DEFAULT 1"),
            ("is_unavailable", "INTEGER DEFAULT 0"),
            ("play_count", "INTEGER DEFAULT 0"),
            ("last_played_at", "TIMESTAMP"),
            ("forward_source_type", "TEXT"),
            ("forward_source_id", "INTEGER"),
            ("forward_source_name", "TEXT"),
            ("forward_source_username", "TEXT"),
            ("uploader_id", "INTEGER"),
        ],
        "users": [
            ("hide_from_search", "INTEGER DEFAULT 0"),
            ("hide_profile", "INTEGER DEFAULT 0"),
            ("notify_subscription", "INTEGER DEFAULT 1"),
        ],
        "user_channels": [
            ("auto_sync", "INTEGER DEFAULT 1"),
        ],
        "playlists": [
            ("pending_cover_url", "TEXT"),
            ("pending_cover_expires_at", "TIMESTAMP"),
        ],
    }

    print(f"[*] Checking database: {db_path}")
    for table_name, columns in schema_definitions.items():
        # Check if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
        if not cursor.fetchone():
            print(f"[-] Table {table_name} does not exist yet (will be created by SQLAlchemy).")
            continue

        # Get existing columns
        cursor.execute(f"PRAGMA table_info({table_name});")
        existing_cols = {row[1] for row in cursor.fetchall()}

        for col_name, col_def in columns:
            if col_name not in existing_cols:
                try:
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def};"
                    print(f"  [+] Adding column: {table_name}.{col_name}")
                    cursor.execute(sql)
                except Exception as e:
                    print(f"  [!] Error adding {table_name}.{col_name}: {e}")

    # Create missing indexes
    indexes = [
        ("idx_channel_message_status", "CREATE INDEX IF NOT EXISTS idx_channel_message_status ON channel_messages(channel_id, status);"),
        ("idx_tracks_normalized_artist", "CREATE INDEX IF NOT EXISTS idx_tracks_normalized_artist ON tracks(normalized_artist);"),
    ]
    for idx_name, idx_sql in indexes:
        try:
            cursor.execute(idx_sql)
        except Exception as e:
            print(f"  [!] Error creating index {idx_name}: {e}")

    conn.commit()
    conn.close()
    print("[✓] SQLite migration completed successfully!")

if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "tg_player.db"
    migrate_sqlite_db(db_file)

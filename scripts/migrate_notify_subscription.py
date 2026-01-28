#!/usr/bin/env python3
"""
Migration script to add notify_subscription column to users table.

Run on server:
    python scripts/migrate_notify_subscription.py
"""
import sqlite3
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import settings

def migrate():
    """Add notify_subscription column to users table if not exists."""
    db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
    
    print(f"Connecting to database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "notify_subscription" in columns:
        print("Column 'notify_subscription' already exists. Nothing to do.")
        conn.close()
        return
    
    print("Adding 'notify_subscription' column to users table...")
    
    # Add the column with default value True
    cursor.execute("""
        ALTER TABLE users 
        ADD COLUMN notify_subscription BOOLEAN DEFAULT 1
    """)
    
    conn.commit()
    print("Migration complete! Column 'notify_subscription' added successfully.")
    
    # Verify
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Current columns: {columns}")
    
    conn.close()


if __name__ == "__main__":
    migrate()

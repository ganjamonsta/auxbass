#!/usr/bin/env python3
"""Check specific track in database"""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "tg_player.db"

track_id = int(sys.argv[1]) if len(sys.argv) > 1 else 4

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
    SELECT t.id, t.title, t.artist, t.enrichment_status,
           e.album_name, e.cover_url, e.genre, e.enriched_at
    FROM tracks t 
    LEFT JOIN track_enrichments e ON t.id = e.track_id 
    WHERE t.id = ?
""", (track_id,))

row = cursor.fetchone()
if row:
    print(f"Track #{row['id']}: {row['artist']} - {row['title']}")
    print(f"  enrichment_status: {row['enrichment_status']}")
    print(f"  album_name: {row['album_name']}")
    print(f"  cover_url: {row['cover_url'][:50] if row['cover_url'] else None}...")
    print(f"  genre: {row['genre']}")
    print(f"  enriched_at: {row['enriched_at']}")
else:
    print(f"Track #{track_id} not found")

conn.close()

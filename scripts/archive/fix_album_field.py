#!/usr/bin/env python3
"""
Fix tracks that were enriched with album in wrong field.
Moves album_name to album field for tracks missing album.

Run from /opt/tg_player: python scripts/fix_album_field.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from shared.database import get_session
from shared.models import Track


async def main():
    print("Checking for tracks with album_name but no album...")
    
    async with get_session() as session:
        # SQLite raw query to check if album_name column exists and has data
        # while album is NULL
        result = await session.execute(text("""
            SELECT id, title, artist, album, genre, cover_url, enrichment_status
            FROM tracks
            WHERE enrichment_status = 'success' 
            AND (album IS NULL OR album = '')
            LIMIT 50
        """))
        tracks = result.fetchall()
    
    if not tracks:
        print("No tracks with missing album field found.")
        return
    
    print(f"Found {len(tracks)} tracks to check")
    for t in tracks[:10]:
        print(f"  - {t.artist} - {t.title}: album={t.album}, status={t.enrichment_status}")
    
    print("\nResetting these tracks to 'pending' for re-enrichment...")
    
    async with get_session() as session:
        # Reset tracks that were "successfully" enriched by the buggy script
        # These have status=success but album is still empty
        result = await session.execute(text("""
            UPDATE tracks
            SET enrichment_status = 'pending'
            WHERE enrichment_status = 'success'
            AND (album IS NULL OR album = '')
        """))
        await session.commit()
        print(f"Reset {result.rowcount} tracks to pending for re-enrichment")


if __name__ == "__main__":
    asyncio.run(main())

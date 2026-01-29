#!/usr/bin/env python3
"""Run this script on the server to check Buerak tracks"""
import asyncio
from shared.database import get_session
from shared.models import Track, UserLibrary, User
from sqlalchemy import select, func, or_

async def check():
    async with get_session() as db:
        # 1. Search by track title "Пролетариат"
        print("=== Searching for 'Пролетариат' in title ===")
        result = await db.execute(
            select(Track.id, Track.title, Track.artist, Track.is_public, Track.is_unavailable)
            .where(func.lower(Track.title).like("%пролетариат%"))
            .limit(10)
        )
        tracks = result.all()
        print(f"Found: {len(tracks)}")
        for t in tracks:
            print(f"  ID={t.id}, '{t.artist}' - '{t.title}', public={t.is_public}")
            # Show hex of artist name
            if t.artist:
                print(f"    Artist hex: {t.artist.encode('utf-8').hex()}")
        
        # 2. Search for anything with "буер" or "buer"
        print("\n=== Searching for 'буер' in artist ===")
        result = await db.execute(
            select(Track.id, Track.title, Track.artist, Track.is_public)
            .where(func.lower(Track.artist).like("%буер%"))
            .limit(10)
        )
        tracks = result.all()
        print(f"Found: {len(tracks)}")
        for t in tracks:
            print(f"  ID={t.id}, '{t.artist}' - '{t.title}'")
        
        # 3. Get tracks from user 696210149 (mmeetthh) - first 10 with Cyrillic artist
        print("\n=== First 20 tracks from @mmeetthh with Cyrillic artists ===")
        result = await db.execute(
            select(Track.id, Track.title, Track.artist)
            .join(UserLibrary, UserLibrary.track_id == Track.id)
            .where(UserLibrary.user_id == 696210149)
            .order_by(UserLibrary.added_at.desc())
            .limit(20)
        )
        tracks = result.all()
        for t in tracks:
            print(f"  {t.artist} - {t.title}")

if __name__ == "__main__":
    asyncio.run(check())

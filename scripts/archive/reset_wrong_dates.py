#!/usr/bin/env python3
"""
Reset release dates that were incorrectly set from wiki.published.
These dates are when the wiki article was edited, not when the album was released.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, and_, update
from shared.database import get_session
from shared.models import Playlist


# Albums that got wrong dates from wiki.published
WRONG_DATES = [
    ("Burial", "Untrue", "2020-10-10"),  # Actually released 2007
    ("Fenech-soler", "Fenech-Soler", "2010-08-08"),  # Might be correct, but verify
    ("Bladee", "Crest", "2022-03-03"),  # Verify - might be close
    ("Bladee", "Eversince", "2021-05-05"),  # Actually 2016
    ("thaiboy digital", "Legendary Member", "2022-03-03"),  # Actually 2018
    ("Calvin Harris", "18 Months", "2022-07-07"),  # Actually 2012
    ("Bladee", "Cold Visions", "2024-07-07"),  # This might be correct (July 2024)
    ("Yung Lean", "Starz", "2023-06-06"),  # Actually 2020
    ("Kelly Bailey", "Half-Life 2: Episode Two", "2019-04-04"),  # Actually 2007
]


async def reset_wrong_dates():
    async with get_session() as session:
        count = 0
        
        for artist, album, wrong_date in WRONG_DATES:
            result = await session.execute(
                select(Playlist)
                .where(
                    and_(
                        Playlist.is_auto_album == True,
                        Playlist.name == album,
                        Playlist.release_date == wrong_date
                    )
                )
            )
            playlists = result.scalars().all()
            
            for pl in playlists:
                print(f"Resetting: {pl.album_artist} - {pl.name} (was {pl.release_date})")
                pl.release_date = None
                count += 1
        
        await session.commit()
        print(f"\nReset {count} albums")


if __name__ == "__main__":
    asyncio.run(reset_wrong_dates())

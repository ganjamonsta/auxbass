#!/usr/bin/env python3
"""
Test enrichment for specific tracks to understand why they get wrong albums.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.services.metadata import metadata_service


async def test():
    # Test problematic tracks
    test_tracks = [
        ("Trial", "Bladee"),
        ("FALSE", "Bladee"),
        ("100s", "Bladee"),
        ("Exstasia", "Bladee"),
        ("DANCE LIKE U IN PAIN", "Bladee"),
        ("GOD SYSTEM", "Bladee"),
        ("SHOW OFF", "Bladee"),
    ]
    
    for title, artist in test_tracks:
        print(f"\n{'='*60}")
        print(f"Testing: {artist} - {title}")
        print('='*60)
        
        # Test Last.fm directly
        lastfm = await metadata_service.search_lastfm_track(title, artist)
        if lastfm:
            print(f"Last.fm: album='{lastfm.get('album')}', artist='{lastfm.get('artist')}'")
        else:
            print("Last.fm: NOT FOUND")
        
        # Test Deezer directly
        deezer = await metadata_service.search_deezer(title, artist)
        if deezer:
            print(f"Deezer: album='{deezer.get('album')}', artist='{deezer.get('artist')}', album_id={deezer.get('album_id')}")
        else:
            print("Deezer: NOT FOUND")
        
        # Test full enrichment
        full = await metadata_service.enrich_track(title, artist)
        print(f"Final result: album='{full.get('album')}', source='{full.get('source')}', enriched={full.get('enriched')}")


if __name__ == "__main__":
    asyncio.run(test())

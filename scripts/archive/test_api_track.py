#!/usr/bin/env python3
"""Test API for specific track"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.services.metadata import metadata_service

async def test(title: str, artist: str):
    print(f"Testing: {artist} - {title}")
    print("="*50)
    
    # Test Last.fm
    print("\n1. Last.fm:")
    lastfm = await metadata_service.search_lastfm_track(title, artist)
    if lastfm:
        print(f"   album: {lastfm.get('album')}")
        print(f"   genre: {lastfm.get('genre')}")
    else:
        print("   NOT FOUND")
    
    # Test Deezer
    print("\n2. Deezer:")
    deezer = await metadata_service.search_deezer(title, artist)
    if deezer:
        print(f"   album: {deezer.get('album')}")
        print(f"   artist: {deezer.get('artist')}")
        print(f"   cover: {deezer.get('cover_url', '')[:50] if deezer.get('cover_url') else None}...")
    else:
        print("   NOT FOUND")
    
    # Test combined
    print("\n3. Combined (enrich_track):")
    result = await metadata_service.enrich_track(title, artist)
    print(f"   album: {result.get('album')}")
    print(f"   source: {result.get('source')}")
    print(f"   enriched: {result.get('enriched')}")
    
    await metadata_service.close()

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        title = sys.argv[1]
        artist = sys.argv[2]
    else:
        title = "Снег идёт"
        artist = "Глюк'oZa"
    
    asyncio.run(test(title, artist))

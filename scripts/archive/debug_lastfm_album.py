#!/usr/bin/env python3
"""
Debug why Last.fm returns album=None for some tracks.
"""
import asyncio
import sys
from pathlib import Path
import aiohttp

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.config import get_settings


async def debug_lastfm_track(title: str, artist: str):
    settings = get_settings()
    api_key = settings.lastfm_api_key
    
    print(f"\n{'='*60}")
    print(f"Testing: {artist} - {title}")
    print('='*60)
    
    async with aiohttp.ClientSession() as session:
        # Test track.getInfo
        params = {
            "method": "track.getInfo",
            "api_key": api_key,
            "artist": artist,
            "track": title,
            "format": "json"
        }
        
        async with session.get("https://ws.audioscrobbler.com/2.0/", params=params) as resp:
            print(f"track.getInfo status: {resp.status}")
            data = await resp.json()
            
            if "error" in data:
                print(f"Error: {data}")
            else:
                track_data = data.get("track", {})
                album = track_data.get("album", {})
                print(f"Track name: {track_data.get('name')}")
                print(f"Artist: {track_data.get('artist')}")
                print(f"Album data: {album}")
                if album:
                    print(f"  Album title: {album.get('title')}")
                    print(f"  Album artist: {album.get('artist')}")
        
        # Try track.search if direct lookup fails or has no album
        print("\n--- Trying track.search ---")
        params = {
            "method": "track.search",
            "api_key": api_key,
            "track": title,
            "artist": artist,
            "format": "json",
            "limit": 5
        }
        
        async with session.get("https://ws.audioscrobbler.com/2.0/", params=params) as resp:
            print(f"track.search status: {resp.status}")
            data = await resp.json()
            
            results = data.get("results", {}).get("trackmatches", {}).get("track", [])
            if isinstance(results, dict):
                results = [results]
            
            print(f"Found {len(results)} results:")
            for i, r in enumerate(results):
                print(f"  {i+1}. {r.get('artist')} - {r.get('name')}")


async def main():
    # Test GOD SYSTEM album tracks
    god_system_tracks = [
        ("DANCE LIKE U IN PAIN", "Bladee"),
        ("GOD SYSTEM", "Bladee"),
        ("SHOW OFF", "Bladee"),
        ("18 WHEELER", "Bladee"),  # This one works
        ("I ABSORB", "Bladee"),  # This one might work
    ]
    
    for title, artist in god_system_tracks:
        await debug_lastfm_track(title, artist)
        await asyncio.sleep(0.3)  # Rate limit


if __name__ == "__main__":
    asyncio.run(main())

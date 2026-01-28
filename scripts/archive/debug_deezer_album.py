#!/usr/bin/env python3
"""
Debug Deezer API for GOD SYSTEM tracks.
"""
import asyncio
import sys
from pathlib import Path
import aiohttp
import urllib.parse

sys.path.insert(0, str(Path(__file__).parent.parent))


async def debug_deezer_track(title: str, artist: str):
    print(f"\n{'='*60}")
    print(f"Testing: {artist} - {title}")
    print('='*60)
    
    async with aiohttp.ClientSession() as session:
        # Clean strings
        clean_title = title.lower().replace("(", "").replace(")", "").replace("prod.", "").strip()
        clean_artist = artist.lower().strip()
        
        # Try specific search
        query = f'track:"{clean_title}" artist:"{clean_artist}"'
        url = f"https://api.deezer.com/search?q={urllib.parse.quote(query)}&limit=10"
        
        print(f"Query: {query}")
        async with session.get(url) as resp:
            print(f"Status: {resp.status}")
            data = await resp.json()
            
            if data.get("data"):
                print(f"Found {len(data['data'])} results:")
                for i, track in enumerate(data["data"][:5]):
                    album = track.get("album", {})
                    print(f"  {i+1}. {track.get('artist', {}).get('name')} - {track.get('title')}")
                    print(f"      Album: {album.get('title')} (id={album.get('id')})")
            else:
                print("No results from specific search")
                
                # Try simple search
                simple_query = f"{clean_artist} {clean_title}"
                url = f"https://api.deezer.com/search?q={urllib.parse.quote(simple_query)}&limit=10"
                print(f"\nTrying simple search: {simple_query}")
                
                async with session.get(url) as resp2:
                    data2 = await resp2.json()
                    if data2.get("data"):
                        print(f"Found {len(data2['data'])} results:")
                        for i, track in enumerate(data2["data"][:5]):
                            album = track.get("album", {})
                            print(f"  {i+1}. {track.get('artist', {}).get('name')} - {track.get('title')}")
                            print(f"      Album: {album.get('title')} (id={album.get('id')})")
                    else:
                        print("No results")


async def main():
    # Test GOD SYSTEM album tracks
    god_system_tracks = [
        ("DANCE LIKE U IN PAIN", "Bladee"),
        ("GOD SYSTEM", "Bladee"),
        ("SHOW OFF", "Bladee"),
        ("18 WHEELER", "Bladee"),
        ("I ABSORB", "Bladee"),
        ("PUPPET MASTER", "Bladee"),  # Known working track
    ]
    
    for title, artist in god_system_tracks:
        await debug_deezer_track(title, artist)
        await asyncio.sleep(0.3)
    
    # Also search for the album directly
    print("\n" + "="*60)
    print("Searching for GOD SYSTEM album directly")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        url = "https://api.deezer.com/search/album?q=bladee%20god%20system&limit=5"
        async with session.get(url) as resp:
            data = await resp.json()
            if data.get("data"):
                for album in data["data"]:
                    print(f"Album: {album.get('title')} by {album.get('artist', {}).get('name')}")
                    print(f"  ID: {album.get('id')}")
                    print(f"  Cover: {album.get('cover_big')}")
            else:
                print("Album not found")


if __name__ == "__main__":
    asyncio.run(main())

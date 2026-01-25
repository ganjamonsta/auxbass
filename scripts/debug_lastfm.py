#!/usr/bin/env python3
"""
Debug script to check what Last.fm returns for album.getInfo
"""

import asyncio
import aiohttp
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import get_settings


async def check_album(artist: str, album: str):
    settings = get_settings()
    
    if not settings.lastfm_api_key:
        print("ERROR: LASTFM_API_KEY not set!")
        return
    
    params = {
        "method": "album.getInfo",
        "api_key": settings.lastfm_api_key,
        "artist": artist,
        "album": album,
        "format": "json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://ws.audioscrobbler.com/2.0/",
            params=params
        ) as resp:
            data = await resp.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python debug_lastfm.py 'Artist' 'Album'")
        print("Example: python debug_lastfm.py 'Burial' 'Untrue'")
        sys.exit(1)
    
    artist = sys.argv[1]
    album = sys.argv[2]
    print(f"Checking: {artist} - {album}\n")
    asyncio.run(check_album(artist, album))

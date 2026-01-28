#!/usr/bin/env python3
"""Debug Deezer search step by step"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.services.metadata import metadata_service

async def test():
    title = "Снег идёт"
    artist = "Глюк'oZa"
    
    print(f"Original: {artist} - {title}")
    print()
    
    # Check what _clean_string does
    clean_title = metadata_service._clean_string(title)
    clean_artist = metadata_service._clean_string(artist)
    
    print(f"_clean_string(title): '{clean_title}'")
    print(f"_clean_string(artist): '{clean_artist}'")
    print()
    
    # The query that will be sent
    query1 = f'track:"{clean_title}" artist:"{clean_artist}"'
    query2 = f"{clean_artist} {clean_title}"
    
    print(f"Query 1: {query1}")
    print(f"Query 2: {query2}")
    print()
    
    # Test with raw aiohttp
    import aiohttp
    async with aiohttp.ClientSession() as session:
        # Test query 1
        async with session.get(
            "https://api.deezer.com/search",
            params={"q": query1, "limit": 3}
        ) as resp:
            data = await resp.json()
            print(f"Query 1 results: {len(data.get('data', []))}")
            for t in data.get('data', [])[:2]:
                print(f"  -> {t['artist']['name']} - {t['title']}")
        
        # Test query 2
        async with session.get(
            "https://api.deezer.com/search",
            params={"q": query2, "limit": 3}
        ) as resp:
            data = await resp.json()
            print(f"Query 2 results: {len(data.get('data', []))}")
            for t in data.get('data', [])[:2]:
                print(f"  -> {t['artist']['name']} - {t['title']}")
    
    await metadata_service.close()

asyncio.run(test())

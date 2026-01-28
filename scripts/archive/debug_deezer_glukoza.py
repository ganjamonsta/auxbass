#!/usr/bin/env python3
"""Debug Deezer search for Глюкоза"""
import asyncio
import aiohttp

async def test():
    async with aiohttp.ClientSession() as session:
        # Test different query formats
        queries = [
            "Глюк'oZa Снег идёт",
            "Глюкоза Снег идёт",
            "Glukoza Снег идёт",
            'track:"Снег идёт" artist:"Глюк\'oZa"',
            'track:"Снег идёт" artist:"Глюкоза"',
            "artist:4570780",  # Direct artist ID
        ]
        
        for q in queries:
            print(f"\nQuery: {q}")
            async with session.get(
                "https://api.deezer.com/search",
                params={"q": q, "limit": 3}
            ) as resp:
                data = await resp.json()
                if data.get("data"):
                    for track in data["data"][:2]:
                        print(f"  -> {track['artist']['name']} - {track['title']} [{track['album']['title']}]")
                else:
                    print(f"  -> NO RESULTS")
                    if data.get("error"):
                        print(f"     Error: {data['error']}")

asyncio.run(test())

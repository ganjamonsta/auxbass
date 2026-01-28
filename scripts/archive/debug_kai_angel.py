#!/usr/bin/env python3
"""
Debug Deezer/Last.fm for Kai Angel GOD SYSTEM album.
"""
import asyncio
import aiohttp
import urllib.parse


async def search_deezer(query: str):
    async with aiohttp.ClientSession() as session:
        url = f"https://api.deezer.com/search?q={urllib.parse.quote(query)}&limit=5"
        async with session.get(url) as resp:
            return await resp.json()


async def search_deezer_album(query: str):
    async with aiohttp.ClientSession() as session:
        url = f"https://api.deezer.com/search/album?q={urllib.parse.quote(query)}&limit=5"
        async with session.get(url) as resp:
            return await resp.json()


async def get_album_tracks(album_id: int):
    async with aiohttp.ClientSession() as session:
        url = f"https://api.deezer.com/album/{album_id}/tracks"
        async with session.get(url) as resp:
            return await resp.json()


async def main():
    print("="*60)
    print("Searching Deezer for Kai Angel")
    print("="*60)
    
    # Search for album
    data = await search_deezer_album("kai angel god system")
    print("\nAlbum search 'kai angel god system':")
    if data.get("data"):
        for album in data["data"]:
            print(f"  {album.get('artist', {}).get('name')} - {album.get('title')}")
            print(f"    ID: {album.get('id')}, Cover: {album.get('cover_medium')}")
    else:
        print("  No results")
    
    # Try track search
    tracks_to_test = [
        "kai angel dance like u in pain",
        "kai angel god system",
        "kai angel show off",
        "kai angel 18 wheeler",
    ]
    
    for query in tracks_to_test:
        print(f"\nTrack search '{query}':")
        data = await search_deezer(query)
        if data.get("data"):
            for track in data["data"][:3]:
                album = track.get("album", {})
                print(f"  {track.get('artist', {}).get('name')} - {track.get('title')}")
                print(f"    Album: {album.get('title')} (id={album.get('id')})")
        else:
            print("  No results")
        await asyncio.sleep(0.25)
    
    # Try "Kai Angel" as artist specifically
    print("\n" + "="*60)
    print("Searching for Kai Angel artist")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        url = "https://api.deezer.com/search/artist?q=kai%20angel&limit=5"
        async with session.get(url) as resp:
            data = await resp.json()
            if data.get("data"):
                for artist in data["data"]:
                    print(f"  Artist: {artist.get('name')} (id={artist.get('id')})")
            else:
                print("  No artists found")


if __name__ == "__main__":
    asyncio.run(main())

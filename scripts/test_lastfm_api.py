#!/usr/bin/env python3
"""
Test script to verify Last.fm API JSON response structure.
Run this on the server to see actual API responses and compare with code.

Usage:
    source .venv/bin/activate
    python scripts/test_lastfm_api.py
    
This verifies:
1. track.getInfo - exact track lookup
2. track.search - track search with results
3. album.getInfo - album metadata and release date
4. JSON normalization - single result as dict vs array handling
"""
import asyncio
import json
import aiohttp
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import get_settings


async def test_track_getinfo(session: aiohttp.ClientSession, api_key: str):
    """Test track.getInfo endpoint"""
    print("\n" + "="*60)
    print("Testing: track.getInfo")
    print("="*60)
    
    params = {
        "method": "track.getInfo",
        "api_key": api_key,
        "artist": "Bladee",
        "track": "Be Nice 2 Me",
        "format": "json"
    }
    
    async with session.get("https://ws.audioscrobbler.com/2.0/", params=params) as resp:
        print(f"Status: {resp.status}")
        data = await resp.json()
        
        # Pretty print structure (without full content)
        if "error" in data:
            print(f"ERROR: {data}")
            return
        
        track = data.get("track", {})
        print(f"\n1. Root key: 'track' present: {bool(track)}")
        
        print(f"\n2. Track fields:")
        print(f"   - name: {track.get('name')}")
        print(f"   - duration: {track.get('duration')} (ms)")
        print(f"   - listeners: {track.get('listeners')}")
        print(f"   - playcount: {track.get('playcount')}")
        
        print(f"\n3. Artist structure:")
        artist = track.get("artist", {})
        print(f"   Type: {type(artist)}")
        if isinstance(artist, dict):
            print(f"   - artist.name: {artist.get('name')}")
            print(f"   - artist.url: {artist.get('url')}")
        else:
            print(f"   VALUE: {artist}")
        
        print(f"\n4. Album structure:")
        album = track.get("album", {})
        print(f"   Type: {type(album)}")
        if isinstance(album, dict):
            print(f"   - album.title: {album.get('title')}")
            print(f"   - album.artist: {album.get('artist')}")
            print(f"   - album.url: {album.get('url')}")
            
            print(f"\n5. Album images:")
            images = album.get("image", [])
            print(f"   Type: {type(images)}")
            print(f"   Count: {len(images)}")
            for i, img in enumerate(images):
                print(f"   [{i}] size={img.get('size')}, #text={img.get('#text', '')[:50]}...")
        
        print(f"\n6. Toptags structure:")
        toptags = track.get("toptags", {})
        print(f"   Type: {type(toptags)}")
        tags = toptags.get("tag", [])
        print(f"   tag Type: {type(tags)}")
        print(f"   tag Count: {len(tags)}")
        for i, tag in enumerate(tags[:5]):
            print(f"   [{i}] name={tag.get('name')}, url={tag.get('url', '')[:30]}...")
        
        print(f"\n7. Wiki structure:")
        wiki = track.get("wiki", {})
        print(f"   Type: {type(wiki)}")
        if wiki:
            print(f"   - published: {wiki.get('published')}")
            print(f"   - summary: {wiki.get('summary', '')[:100]}...")


async def test_track_search(session: aiohttp.ClientSession, api_key: str):
    """Test track.search endpoint"""
    print("\n" + "="*60)
    print("Testing: track.search")
    print("="*60)
    
    params = {
        "method": "track.search",
        "api_key": api_key,
        "track": "Be Nice 2 Me",
        "artist": "Bladee",
        "format": "json",
        "limit": 5
    }
    
    async with session.get("https://ws.audioscrobbler.com/2.0/", params=params) as resp:
        print(f"Status: {resp.status}")
        data = await resp.json()
        
        if "error" in data:
            print(f"ERROR: {data}")
            return
        
        results = data.get("results", {})
        print(f"\n1. Root key 'results' present: {bool(results)}")
        
        print(f"\n2. Results fields:")
        print(f"   - opensearch:totalResults: {results.get('opensearch:totalResults')}")
        print(f"   - opensearch:startIndex: {results.get('opensearch:startIndex')}")
        print(f"   - opensearch:itemsPerPage: {results.get('opensearch:itemsPerPage')}")
        
        trackmatches = results.get("trackmatches", {})
        print(f"\n3. trackmatches structure:")
        print(f"   Type: {type(trackmatches)}")
        
        tracks = trackmatches.get("track", [])
        print(f"\n4. track list:")
        print(f"   Type: {type(tracks)}")
        print(f"   Count: {len(tracks)}")
        
        # Handle case when single result is dict instead of list
        if isinstance(tracks, dict):
            tracks = [tracks]
            print("   NOTE: Single result returned as dict, not list!")
        
        for i, t in enumerate(tracks[:3]):
            print(f"\n   [{i}] Track:")
            print(f"       name: {t.get('name')}")
            print(f"       artist: {t.get('artist')}")
            print(f"       url: {t.get('url')}")
            print(f"       listeners: {t.get('listeners')}")


async def test_album_getinfo(session: aiohttp.ClientSession, api_key: str):
    """Test album.getInfo endpoint"""
    print("\n" + "="*60)
    print("Testing: album.getInfo")
    print("="*60)
    
    params = {
        "method": "album.getInfo",
        "api_key": api_key,
        "artist": "Bladee",
        "album": "Red Light",
        "format": "json"
    }
    
    async with session.get("https://ws.audioscrobbler.com/2.0/", params=params) as resp:
        print(f"Status: {resp.status}")
        data = await resp.json()
        
        if "error" in data:
            print(f"ERROR: {data}")
            return
        
        album = data.get("album", {})
        print(f"\n1. Root key 'album' present: {bool(album)}")
        
        print(f"\n2. Album fields:")
        print(f"   - name: {album.get('name')}")
        print(f"   - artist: {album.get('artist')}")
        print(f"   - url: {album.get('url')}")
        print(f"   - listeners: {album.get('listeners')}")
        print(f"   - playcount: {album.get('playcount')}")
        
        print(f"\n3. Tags structure:")
        tags_obj = album.get("tags", {})
        print(f"   Type of tags: {type(tags_obj)}")
        tags = tags_obj.get("tag", [])
        print(f"   Type of tag list: {type(tags)}")
        print(f"   Count: {len(tags)}")
        for i, tag in enumerate(tags[:5]):
            print(f"   [{i}] name={tag.get('name')}")
        
        # Check for year tags
        year_tags = [t.get("name") for t in tags if t.get("name", "").isdigit() and len(t.get("name", "")) == 4]
        print(f"\n4. Year tags found: {year_tags}")
        
        print(f"\n5. Wiki structure:")
        wiki = album.get("wiki", {})
        print(f"   Type: {type(wiki)}")
        if wiki:
            print(f"   - published: {wiki.get('published')}")
            content = wiki.get('content', '')
            print(f"   - content (first 200 chars): {content[:200]}...")
        
        print(f"\n6. Images:")
        images = album.get("image", [])
        print(f"   Count: {len(images)}")
        for i, img in enumerate(images):
            print(f"   [{i}] size={img.get('size')}, url={img.get('#text', '')[:50]}...")


async def main():
    settings = get_settings()
    
    if not settings.lastfm_api_key:
        print("ERROR: lastfm_api_key not configured in .env")
        return
    
    print(f"Last.fm API Key: {settings.lastfm_api_key[:8]}...")
    
    async with aiohttp.ClientSession() as session:
        await test_track_getinfo(session, settings.lastfm_api_key)
        await test_track_search(session, settings.lastfm_api_key)
        await test_album_getinfo(session, settings.lastfm_api_key)
    
    print("\n" + "="*60)
    print("Testing complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

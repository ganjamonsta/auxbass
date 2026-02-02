"""
Explore Last.fm tags API to understand what kind of tags are available.
"""
import asyncio
import aiohttp
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.config import get_settings

BASE_URL = "https://ws.audioscrobbler.com/2.0/"

# Test cases: different genres/scenes
TEST_ARTISTS = [
    "Bladee",           # Cloud rap / drain gang
    "Yung Lean",        # Cloud rap / sad boys
    "Crystal Castles",  # Witch house / electronic
    "Burial",           # UK garage / dubstep
    "Playboi Carti",    # Trap / rage beats
    "Bones",            # Cloud rap / underground
    "Death Grips",      # Experimental hip-hop
    "Молчат Дома",      # Post-punk / Russian
    "IC3PEAK",          # Russian experimental
    "Pharaoh",          # Russian rap
    "Кровосток",        # Russian rap
    "FACE",             # Russian rap
]

TEST_TRACKS = [
    ("Bladee", "Obedient"),
    ("Yung Lean", "Ginseng Strip 2002"),
    ("Crystal Castles", "Crimewave"),
    ("Burial", "Archangel"),
    ("Playboi Carti", "Magnolia"),
    ("Death Grips", "Guillotine"),
    ("Молчат Дома", "Судно"),
    ("IC3PEAK", "Смерти Больше Нет"),
]


async def get_artist_top_tags(session, api_key: str, artist: str):
    """Get top tags for an artist"""
    params = {
        "method": "artist.getTopTags",
        "artist": artist,
        "api_key": api_key,
        "format": "json"
    }
    
    async with session.get(BASE_URL, params=params) as resp:
        if resp.status == 200:
            data = await resp.json()
            if "toptags" in data:
                return data["toptags"].get("tag", [])
    return []


async def get_track_top_tags(session, api_key: str, artist: str, track: str):
    """Get top tags for a track"""
    params = {
        "method": "track.getTopTags",
        "artist": artist,
        "track": track,
        "api_key": api_key,
        "format": "json"
    }
    
    async with session.get(BASE_URL, params=params) as resp:
        if resp.status == 200:
            data = await resp.json()
            if "toptags" in data:
                return data["toptags"].get("tag", [])
    return []


async def get_artist_info_tags(session, api_key: str, artist: str):
    """Get tags from artist.getInfo (less tags but curated)"""
    params = {
        "method": "artist.getInfo",
        "artist": artist,
        "api_key": api_key,
        "format": "json"
    }
    
    async with session.get(BASE_URL, params=params) as resp:
        if resp.status == 200:
            data = await resp.json()
            if "artist" in data:
                tag_data = data["artist"].get("tags", {}).get("tag", [])
                if isinstance(tag_data, dict):
                    return [tag_data]
                return tag_data
    return []


async def main():
    settings = get_settings()
    
    if not settings.lastfm_api_key:
        print("ERROR: LASTFM_API_KEY not set in .env!")
        return
    
    api_key = settings.lastfm_api_key
    print(f"Using API key: {api_key[:8]}...\n")
    
    async with aiohttp.ClientSession() as session:
        # Test artist tags
        print("=" * 60)
        print("ARTIST TOP TAGS (artist.getTopTags)")
        print("=" * 60)
        
        for artist in TEST_ARTISTS:
            print(f"\n🎤 {artist}:")
            tags = await get_artist_top_tags(session, api_key, artist)
            
            if tags:
                # Show top 10 tags with count
                for i, tag in enumerate(tags[:10]):
                    name = tag.get("name", "")
                    count = tag.get("count", 0)
                    print(f"   {i+1}. {name} (count: {count})")
            else:
                print("   [No tags found]")
            
            await asyncio.sleep(0.3)  # Rate limit
        
        print("\n")
        print("=" * 60)
        print("TRACK TOP TAGS (track.getTopTags)")
        print("=" * 60)
        
        for artist, track in TEST_TRACKS:
            print(f"\n🎵 {artist} - {track}:")
            tags = await get_track_top_tags(session, api_key, artist, track)
            
            if tags:
                for i, tag in enumerate(tags[:10]):
                    name = tag.get("name", "")
                    count = tag.get("count", 0)
                    print(f"   {i+1}. {name} (count: {count})")
            else:
                print("   [No tags found]")
            
            await asyncio.sleep(0.3)
        
        print("\n")
        print("=" * 60)
        print("COMPARISON: artist.getInfo vs artist.getTopTags")
        print("=" * 60)
        
        for artist in TEST_ARTISTS[:4]:
            print(f"\n🎤 {artist}:")
            
            info_tags = await get_artist_info_tags(session, api_key, artist)
            await asyncio.sleep(0.2)
            top_tags = await get_artist_top_tags(session, api_key, artist)
            
            print("   getInfo tags:", [t.get("name") for t in info_tags[:5]])
            print("   getTopTags:  ", [t.get("name") for t in top_tags[:5]])
            
            await asyncio.sleep(0.3)


if __name__ == "__main__":
    asyncio.run(main())

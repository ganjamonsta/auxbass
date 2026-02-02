"""
Analyze Last.fm tags to find garbage/spam tags patterns.
"""
import asyncio
import aiohttp
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.config import get_settings

BASE_URL = "https://ws.audioscrobbler.com/2.0/"

# Diverse set of artists to analyze tag patterns
TEST_ARTISTS = [
    # Cloud rap / underground
    "Bladee", "Yung Lean", "Bones", "Ecco2k", "Thaiboy Digital",
    # Mainstream rap  
    "Travis Scott", "Kanye West", "Drake", "Kendrick Lamar",
    # Electronic
    "Burial", "Aphex Twin", "Crystal Castles", "Salem",
    # Russian
    "Молчат Дома", "IC3PEAK", "Кровосток", "Oxxxymiron", "Скриптонит",
    # Rock/Alternative
    "Radiohead", "Nirvana", "The Strokes",
    # Pop
    "Charli XCX", "100 gecs", "SOPHIE",
]


async def get_artist_top_tags(session, api_key: str, artist: str):
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


def is_likely_garbage(tag: str, count: int) -> tuple[bool, str]:
    """
    Detect garbage tags with reason.
    Returns (is_garbage, reason)
    """
    tag_lower = tag.lower().strip()
    
    # Very low count (unless it's the only tag)
    if count < 3:
        return True, "low_count"
    
    # Contains profanity/spam words
    spam_words = ["poop", "piss", "shit", "fuck", "govno", "liar", "nigga", "bitch"]
    for word in spam_words:
        if word in tag_lower:
            return True, "profanity"
    
    # Too long (likely a meme/sentence)
    if len(tag) > 30:
        return True, "too_long"
    
    # Contains "best" or "favorite" (personal opinion, not genre)
    personal_words = ["best", "favorite", "favourite", "love", "my ", "i "]
    for word in personal_words:
        if word in tag_lower:
            return True, "personal"
    
    # Artist name as tag (useless)
    # This would need context (the artist name) to check
    
    return False, ""


async def main():
    settings = get_settings()
    if not settings.lastfm_api_key:
        print("ERROR: LASTFM_API_KEY not set!")
        return
    
    api_key = settings.lastfm_api_key
    all_tags = Counter()
    garbage_tags = []
    good_tags = []
    
    async with aiohttp.ClientSession() as session:
        for artist in TEST_ARTISTS:
            tags = await get_artist_top_tags(session, api_key, artist)
            
            for tag in tags[:15]:  # Check top 15 tags per artist
                name = tag.get("name", "")
                count = tag.get("count", 0)
                
                all_tags[name.lower()] += 1
                
                is_garbage, reason = is_likely_garbage(name, count)
                if is_garbage:
                    garbage_tags.append((name, count, reason, artist))
                else:
                    good_tags.append((name, count))
            
            await asyncio.sleep(0.25)
        
        # Print results
        print("=" * 70)
        print("GARBAGE TAGS DETECTED")
        print("=" * 70)
        for name, count, reason, artist in sorted(garbage_tags, key=lambda x: x[2]):
            print(f"  [{reason:12}] {name:40} (count={count}, artist={artist})")
        
        print("\n")
        print("=" * 70)
        print("MOST COMMON TAGS (good ones)")
        print("=" * 70)
        # Filter out garbage from counter
        garbage_names = {t[0].lower() for t in garbage_tags}
        good_counter = Counter({k: v for k, v in all_tags.items() if k not in garbage_names})
        
        for tag, freq in good_counter.most_common(50):
            print(f"  {freq:3}x  {tag}")
        
        print("\n")
        print("=" * 70)
        print("INTERESTING NICHE TAGS (appear 1-3 times)")
        print("=" * 70)
        niche = [(t, c) for t, c in all_tags.items() if 1 <= c <= 3 and t not in garbage_names]
        for tag, freq in sorted(niche, key=lambda x: x[0])[:40]:
            print(f"  {freq}x  {tag}")


if __name__ == "__main__":
    asyncio.run(main())

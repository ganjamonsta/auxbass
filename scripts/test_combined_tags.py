"""
Test the new get_combined_tags method.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.services.enrichment import lastfm_client


async def main():
    print("Testing get_combined_tags method\n")
    print("=" * 60)
    
    test_cases = [
        ("Obedient", "Bladee"),
        ("Ginseng Strip 2002", "Yung Lean"),
        ("Crimewave", "Crystal Castles"),
        ("Archangel", "Burial"),  # Track has no tags, should fallback to artist
        ("Судно", "Молчат Дома"),
        ("Magnolia", "Playboi Carti"),
    ]
    
    for title, artist in test_cases:
        print(f"\n🎵 {artist} - {title}")
        
        tags = await lastfm_client.get_combined_tags(title, artist)
        
        if tags:
            print(f"   Tags: {tags}")
        else:
            print("   [No tags found]")
        
        await asyncio.sleep(0.5)  # Rate limiting
    
    await lastfm_client.close()
    print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())

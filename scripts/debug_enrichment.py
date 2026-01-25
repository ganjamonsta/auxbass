#!/usr/bin/env python3
"""
Debug enrichment for a specific track.
Shows what Deezer returns and why matching might fail.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.services.metadata import metadata_service


async def test_search(artist: str, title: str):
    """Test Deezer search and show results."""
    print(f"\n{'='*60}")
    print(f"Testing: {artist} - {title}")
    print(f"{'='*60}")
    
    # Show what cleaned strings look like
    clean_title = metadata_service._clean_string(title)
    clean_artist = metadata_service._clean_string(artist)
    norm_artist = metadata_service._normalize_artist(artist)
    
    print(f"\nCleaned title:  '{title}' -> '{clean_title}'")
    print(f"Cleaned artist: '{artist}' -> '{clean_artist}'")
    print(f"Normalized artist: '{artist}' -> '{norm_artist}'")
    
    # Do raw Deezer search
    session = await metadata_service._get_session()
    await metadata_service._rate_limit()
    
    query = f'track:"{clean_title}" artist:"{clean_artist}"'
    print(f"\nDeezer query: {query}")
    
    async with session.get(
        f"{metadata_service.DEEZER_API}/search",
        params={"q": query, "limit": 5}
    ) as resp:
        if resp.status != 200:
            print(f"ERROR: Deezer returned {resp.status}")
            return
        
        data = await resp.json()
    
    if not data.get("data"):
        print("\nNo results from Deezer!")
        
        # Try simpler search
        print(f"\nTrying simpler query: '{clean_artist} {clean_title}'")
        await metadata_service._rate_limit()
        
        async with session.get(
            f"{metadata_service.DEEZER_API}/search",
            params={"q": f"{clean_artist} {clean_title}", "limit": 5}
        ) as resp2:
            if resp2.status == 200:
                data = await resp2.json()
    
    if not data.get("data"):
        print("\nStill no results!")
        return
    
    print(f"\nDeezer returned {len(data['data'])} results:")
    
    for i, track in enumerate(data["data"], 1):
        deezer_title = track.get("title", "")
        deezer_artist = track.get("artist", {}).get("name", "")
        deezer_album = track.get("album", {}).get("title", "")
        
        # Check if artist matches
        matches = metadata_service._artist_matches(artist, deezer_artist)
        norm_deezer = metadata_service._normalize_artist(deezer_artist)
        
        match_icon = "✓" if matches else "✗"
        
        print(f"\n  {i}. {deezer_artist} - {deezer_title}")
        print(f"     Album: {deezer_album}")
        print(f"     Artist match: {match_icon} ('{norm_artist}' vs '{norm_deezer}')")
    
    # Now test actual enrichment
    print(f"\n{'='*60}")
    print("Testing full enrichment:")
    print(f"{'='*60}")
    
    result = await metadata_service.enrich_track(title, artist)
    
    if result.get("enriched"):
        print(f"\n✓ Enriched successfully!")
        print(f"  Album: {result.get('album')}")
        print(f"  Genre: {result.get('genre')}")
        print(f"  Cover: {result.get('cover_url', '')[:50]}...")
    else:
        print(f"\n✗ Enrichment failed!")


async def main():
    # Test cases
    test_cases = [
        ("Dubsidia", "Pasta Gangsta"),
        ("Dubsidia", "Elekktroshockk (Original Mix)"),
        ("Dubsidia", "Orisa"),
        ("BLADEE", "D-925 prod. Forza"),
        ("ECCO2K", "guardianAngels((NO2))"),
        ("Bladee", "Flatline"),
    ]
    
    for artist, title in test_cases:
        await test_search(artist, title)
    
    await metadata_service.close()


if __name__ == "__main__":
    asyncio.run(main())

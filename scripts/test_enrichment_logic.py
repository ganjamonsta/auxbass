#!/usr/bin/env python3
"""Quick test of enrichment logic"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.services.metadata import metadata_service

async def test():
    print("="*50)
    print("TESTING ENRICHMENT LOGIC")
    print("Last.fm = PRIMARY, Deezer = fallback")
    print("="*50)
    
    tests = [
        ("FALSE", "Bladee"),      # Should be Cold Visions
        ("Trial", "Bladee"),      # Should be Bladeecity  
        ("Be In Your Mind", "Bladee"),  # Should be 333
        ("RAIN CHECK", "Bladee"),       # Should be Crest (feat Ecco2k)
    ]
    
    for title, artist in tests:
        result = await metadata_service.enrich_track(title, artist)
        print(f"\n{artist} - {title}:")
        print(f"  album: {result.get('album')}")
        print(f"  source: {result.get('source')}")
        print(f"  enriched: {result.get('enriched')}")
    
    await metadata_service.close()
    print("\n" + "="*50)
    print("TEST COMPLETE")

if __name__ == "__main__":
    asyncio.run(test())

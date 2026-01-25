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
        print("\nNo results from specific search!")
        
        # Try simpler search
        simple_query = f"{clean_artist} {clean_title}"
        print(f"\nTrying simpler query: '{simple_query}'")
        await metadata_service._rate_limit()
        
        async with session.get(
            f"{metadata_service.DEEZER_API}/search",
            params={"q": simple_query, "limit": 5}
        ) as resp2:
            if resp2.status == 200:
                data = await resp2.json()
    
    if not data.get("data"):
        print("\nStill no results from search!")
        
        # Try searching by just artist to see what's available
        print(f"\nSearching for artist only: '{clean_artist}'")
        await metadata_service._rate_limit()
        
        async with session.get(
            f"{metadata_service.DEEZER_API}/search/artist",
            params={"q": clean_artist, "limit": 3}
        ) as resp3:
            if resp3.status == 200:
                artist_data = await resp3.json()
                if artist_data.get("data"):
                    for a in artist_data["data"]:
                        print(f"  Found artist: {a.get('name')} (id: {a.get('id')})")
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


async def test_album_direct(album_id: int):
    """Test fetching album directly by ID."""
    print(f"\n{'='*60}")
    print(f"Fetching album directly: {album_id}")
    print(f"{'='*60}")
    
    session = await metadata_service._get_session()
    await metadata_service._rate_limit()
    
    async with session.get(
        f"{metadata_service.DEEZER_API}/album/{album_id}"
    ) as resp:
        if resp.status != 200:
            print(f"ERROR: {resp.status}")
            return
        
        data = await resp.json()
    
    print(f"\nAlbum: {data.get('title')}")
    print(f"Artist: {data.get('artist', {}).get('name')}")
    print(f"Release: {data.get('release_date')}")
    
    # Get tracks
    await metadata_service._rate_limit()
    async with session.get(
        f"{metadata_service.DEEZER_API}/album/{album_id}/tracks"
    ) as resp2:
        if resp2.status == 200:
            tracks_data = await resp2.json()
            print(f"\nTracks ({len(tracks_data.get('data', []))}):")
            for t in tracks_data.get("data", []):
                print(f"  {t.get('track_position')}. {t.get('title')}")


async def test_album_search(artist: str, title: str):
    """Try searching via album instead of track."""
    print(f"\n{'='*60}")
    print(f"Album-based search: {artist} - {title}")
    print(f"{'='*60}")
    
    session = await metadata_service._get_session()
    
    # Try searching for artist's albums
    await metadata_service._rate_limit()
    
    # First find the artist
    async with session.get(
        f"{metadata_service.DEEZER_API}/search/artist",
        params={"q": artist, "limit": 5}
    ) as resp:
        if resp.status != 200:
            print(f"ERROR: {resp.status}")
            return
        data = await resp.json()
    
    if not data.get("data"):
        print("Artist not found!")
        return
    
    # Find matching artist
    target_artist = None
    norm_artist = metadata_service._normalize_artist(artist)
    
    for a in data["data"]:
        a_name = a.get("name", "")
        if metadata_service._normalize_artist(a_name) == norm_artist:
            target_artist = a
            break
    
    if not target_artist:
        print(f"No exact artist match. Found: {[a.get('name') for a in data['data']]}")
        # Try first one anyway
        target_artist = data["data"][0]
    
    print(f"Found artist: {target_artist.get('name')} (id: {target_artist.get('id')})")
    
    # Get artist's albums
    artist_id = target_artist.get("id")
    await metadata_service._rate_limit()
    
    async with session.get(
        f"{metadata_service.DEEZER_API}/artist/{artist_id}/albums",
        params={"limit": 50}
    ) as resp:
        if resp.status != 200:
            print(f"ERROR getting albums: {resp.status}")
            return
        albums_data = await resp.json()
    
    print(f"\nArtist has {len(albums_data.get('data', []))} albums")
    
    # Search for the track in each album
    clean_title = metadata_service._clean_string(title).lower()
    
    for album in albums_data.get("data", [])[:20]:  # Check first 20 albums
        album_id = album.get("id")
        album_title = album.get("title")
        
        await metadata_service._rate_limit()
        
        async with session.get(
            f"{metadata_service.DEEZER_API}/album/{album_id}/tracks"
        ) as resp:
            if resp.status != 200:
                continue
            tracks_data = await resp.json()
        
        for track in tracks_data.get("data", []):
            track_title = track.get("title", "")
            if clean_title in track_title.lower() or track_title.lower() in clean_title:
                print(f"\n✓ FOUND: '{track_title}' in album '{album_title}'")
                print(f"  Album ID: {album_id}")
                print(f"  Track ID: {track.get('id')}")
                return album_id, track
    
    print("\nTrack not found in any album!")
    return None


async def main():
    # First, check the Cold Visions album directly
    await test_album_direct(698241761)
    
    # Test regular search
    test_cases = [
        ("Bladee", "Flatline"),
    ]
    
    for artist, title in test_cases:
        await test_search(artist, title)
    
    # Now try album-based search
    print("\n" + "="*60)
    print("TRYING ALBUM-BASED SEARCH APPROACH")
    print("="*60)
    
    await test_album_search("Bladee", "FLATLINE")
    
    await metadata_service.close()


if __name__ == "__main__":
    asyncio.run(main())

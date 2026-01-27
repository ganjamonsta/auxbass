#!/usr/bin/env python3
"""
Diagnose why some tracks were not enriched correctly.
"""
import asyncio
import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent / "tg_player.db"


def analyze_failed_enrichments():
    """Find patterns in failed enrichments."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 80)
    print("ENRICHMENT FAILURE ANALYSIS")
    print("=" * 80)
    
    # 1. Count by enrichment status
    print("\n1. ENRICHMENT STATUS DISTRIBUTION:")
    cursor.execute("""
        SELECT 
            enrichment_status as status,
            COUNT(*) as cnt
        FROM tracks
        GROUP BY status
        ORDER BY cnt DESC
    """)
    for row in cursor.fetchall():
        print(f"   {row['status']}: {row['cnt']}")
    
    # 2. Tracks with NULL album_name despite enriched status
    print("\n2. ENRICHED BUT NO ALBUM NAME:")
    cursor.execute("""
        SELECT t.id, t.title, t.artist, t.enrichment_status, e.album_name
        FROM tracks t
        JOIN track_enrichments e ON t.id = e.track_id
        WHERE t.enrichment_status = 'enriched' AND (e.album_name IS NULL OR e.album_name = '')
        LIMIT 20
    """)
    for row in cursor.fetchall():
        print(f"   [{row['id']}] {row['artist']} - {row['title']}")
        print(f"       Status: {row['enrichment_status']}, Album: {row['album_name']}")
    
    # 3. Failed enrichments
    print("\n3. FAILED ENRICHMENTS (sample):")
    cursor.execute("""
        SELECT t.id, t.title, t.artist, t.enrichment_status
        FROM tracks t
        WHERE t.enrichment_status = 'failed'
        LIMIT 20
    """)
    for row in cursor.fetchall():
        print(f"   [{row['id']}] {row['artist']} - {row['title']}")
    
    # 4. Tracks with NO enrichment record at all
    print("\n4. TRACKS WITHOUT ENRICHMENT RECORD:")
    cursor.execute("""
        SELECT t.id, t.title, t.artist, t.created_at
        FROM tracks t
        LEFT JOIN track_enrichments e ON t.id = e.track_id
        WHERE e.id IS NULL
        LIMIT 20
    """)
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f"   [{row['id']}] {row['artist']} - {row['title']}")
    else:
        print("   (none)")
    
    # 5. GOD SYSTEM tracks specifically
    print("\n5. BLADEE 'GOD SYSTEM' ALBUM TRACKS:")
    cursor.execute("""
        SELECT t.id, t.title, t.artist, e.album_name, t.enrichment_status
        FROM tracks t
        LEFT JOIN track_enrichments e ON t.id = e.track_id
        WHERE t.artist LIKE '%bladee%'
        ORDER BY t.title
    """)
    god_system_tracks = [
        "18 WHEELER", "DANCE LIKE U IN PAIN", "DESTINY BOND", "FLEX MUZIK 3",
        "GIRL FANTASY", "GOD SYSTEM", "HARDCORE DRAIN", "I ABSORB", "LIQUID STEEL", 
        "OBJECT PERMANENCE", "PUPPET MASTER", "RAT PACK", "SHOW OFF"
    ]
    for row in cursor.fetchall():
        marker = ""
        if row['title'].upper() in [t.upper() for t in god_system_tracks]:
            if row['album_name'] != "GOD SYSTEM":
                marker = " *** WRONG ALBUM ***"
        print(f"   [{row['id']}] {row['title']}")
        print(f"       Album: {row['album_name']}, Status: {row['enrichment_status']}{marker}")
    
    # 6. Tracks wrongly assigned to '333' album
    print("\n6. TRACKS WITH ENRICHMENT ALBUM='333':")
    cursor.execute("""
        SELECT t.id, t.title, t.artist, e.album_name
        FROM tracks t
        JOIN track_enrichments e ON t.id = e.track_id
        WHERE e.album_name = '333'
        ORDER BY t.artist, t.title
    """)
    # True 333 tracks from Last.fm
    true_333_tracks = [
        "333", "3RD Crusher", "Always", "BurnOut", "Crushed", "Day 2 Day",
        "Desire Is A Trap", "DNA Rain", "F.U.S.S.", "Girls Just Want to Have Fun",
        "I.e.e.2", "Paranoid", "Salute", "Thaiboy", "Victim", "You Lose"
    ]
    for row in cursor.fetchall():
        title = row['title']
        is_correct = any(title.lower() == t.lower() for t in true_333_tracks)
        marker = "" if is_correct else " *** NOT IN 333 ***"
        print(f"   [{row['id']}] {row['artist']} - {title}{marker}")
    
    conn.close()


async def test_enrichment_live():
    """Test enrichment on problematic tracks."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from bot.services.metadata import metadata_service
    
    print("\n" + "=" * 80)
    print("LIVE ENRICHMENT TEST")
    print("=" * 80)
    
    # Test problematic tracks
    test_tracks = [
        ("DANCE LIKE U IN PAIN", "Bladee"),
        ("GOD SYSTEM", "Bladee"),
        ("SHOW OFF", "Bladee"),
        ("Trial", "Bladee"),  # Should NOT be in 333
        ("FALSE", "Bladee"),  # Should NOT be in 333
    ]
    
    for title, artist in test_tracks:
        print(f"\n>>> Testing: {artist} - {title}")
        
        # Test Last.fm directly
        lastfm_result = await metadata_service.search_lastfm_track(title, artist)
        print(f"   Last.fm: {lastfm_result}")
        
        # Test Deezer directly
        deezer_result = await metadata_service.search_deezer(title, artist)
        print(f"   Deezer: {deezer_result}")
        
        # Test full enrichment
        full_result = await metadata_service.enrich_track(title, artist)
        print(f"   Full enrichment: album={full_result.get('album')}, source={full_result.get('source')}")


if __name__ == "__main__":
    analyze_failed_enrichments()
    
    # Uncomment to test live enrichment
    # asyncio.run(test_enrichment_live())

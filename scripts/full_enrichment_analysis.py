#!/usr/bin/env python3
"""
Full analysis of enrichment problems in the database.
"""
import sqlite3
from pathlib import Path
from collections import Counter

DB_PATH = Path(__file__).parent.parent / "tg_player.db"


def analyze():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("="*80)
    print("FULL DATABASE ENRICHMENT ANALYSIS")
    print("="*80)
    
    # 1. Overall stats
    print("\n1. OVERALL STATS:")
    cursor.execute("SELECT COUNT(*) FROM tracks")
    total_tracks = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM track_enrichments")
    total_enrichments = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM track_enrichments WHERE album_name IS NOT NULL AND album_name != ''")
    with_album = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM albums")
    total_albums = cursor.fetchone()[0]
    
    print(f"   Total tracks: {total_tracks}")
    print(f"   Tracks with enrichment: {total_enrichments}")
    print(f"   Tracks with album_name: {with_album}")
    print(f"   Total albums: {total_albums}")
    
    # 2. Enrichment status breakdown
    print("\n2. ENRICHMENT STATUS:")
    cursor.execute("""
        SELECT enrichment_status, COUNT(*) as cnt 
        FROM tracks 
        GROUP BY enrichment_status
    """)
    for row in cursor.fetchall():
        pct = row['cnt'] / total_tracks * 100
        print(f"   {row['enrichment_status']}: {row['cnt']} ({pct:.1f}%)")
    
    # 3. Top artists without album enrichment
    print("\n3. TOP ARTISTS WITH MISSING ALBUM DATA:")
    cursor.execute("""
        SELECT t.artist, COUNT(*) as cnt
        FROM tracks t
        LEFT JOIN track_enrichments e ON t.id = e.track_id
        WHERE t.enrichment_status = 'completed' 
          AND (e.album_name IS NULL OR e.album_name = '')
        GROUP BY t.artist
        ORDER BY cnt DESC
        LIMIT 15
    """)
    for row in cursor.fetchall():
        print(f"   {row['artist']}: {row['cnt']} tracks without album")
    
    # 4. Albums with potential wrong tracks
    print("\n4. ALBUMS WITH SUSPICIOUS TRACK COUNTS:")
    cursor.execute("""
        SELECT a.id, a.name, a.artist, a.total_tracks, 
               COUNT(at.track_id) as actual_tracks,
               a.deezer_album_id
        FROM albums a
        LEFT JOIN album_tracks at ON a.id = at.album_id
        GROUP BY a.id
        HAVING actual_tracks > 0 
           AND total_tracks IS NOT NULL 
           AND actual_tracks != total_tracks
        ORDER BY ABS(actual_tracks - total_tracks) DESC
        LIMIT 20
    """)
    print(f"   {'Album':<30} {'Artist':<20} {'Expected':<10} {'Actual':<10} {'Deezer ID'}")
    for row in cursor.fetchall():
        diff = row['actual_tracks'] - (row['total_tracks'] or 0)
        sign = '+' if diff > 0 else ''
        print(f"   {row['name'][:29]:<30} {row['artist'][:19]:<20} {row['total_tracks'] or '?':<10} {row['actual_tracks']:<10} {row['deezer_album_id'] or 'N/A'}")
    
    # 5. Albums without deezer_album_id
    print("\n5. ALBUMS WITHOUT DEEZER ID (can't validate tracklist):")
    cursor.execute("""
        SELECT a.id, a.name, a.artist, COUNT(at.track_id) as track_count
        FROM albums a
        LEFT JOIN album_tracks at ON a.id = at.album_id
        WHERE a.deezer_album_id IS NULL
        GROUP BY a.id
        HAVING track_count > 0
        ORDER BY track_count DESC
        LIMIT 20
    """)
    for row in cursor.fetchall():
        print(f"   [{row['id']}] {row['artist']} - {row['name']} ({row['track_count']} tracks)")
    
    # 6. Potential duplicate albums
    print("\n6. POTENTIAL DUPLICATE ALBUMS (same name, different artist spelling):")
    cursor.execute("""
        SELECT normalized_name, COUNT(*) as cnt, GROUP_CONCAT(artist, ' | ') as artists
        FROM albums
        GROUP BY normalized_name
        HAVING cnt > 1
        ORDER BY cnt DESC
        LIMIT 15
    """)
    for row in cursor.fetchall():
        print(f"   '{row['normalized_name']}' ({row['cnt']}x): {row['artists']}")
    
    # 7. Tracks assigned to wrong albums (enrichment album_name != album_tracks album)
    print("\n7. TRACKS WITH MISMATCHED ALBUM ASSIGNMENT:")
    cursor.execute("""
        SELECT t.id, t.title, t.artist, e.album_name as enrichment_album, a.name as assigned_album
        FROM tracks t
        JOIN track_enrichments e ON t.id = e.track_id
        JOIN album_tracks at ON t.id = at.track_id
        JOIN albums a ON at.album_id = a.id
        WHERE e.album_name IS NOT NULL 
          AND e.album_name != ''
          AND LOWER(e.album_name) != LOWER(a.name)
        LIMIT 20
    """)
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f"   [{row['id']}] {row['artist']} - {row['title']}")
            print(f"       Enrichment says: '{row['enrichment_album']}' but assigned to: '{row['assigned_album']}'")
    else:
        print("   (none found)")
    
    conn.close()


if __name__ == "__main__":
    analyze()

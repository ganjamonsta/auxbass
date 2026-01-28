#!/usr/bin/env python3
"""Analyze albums state in the database"""
import sqlite3

conn = sqlite3.connect('tg_player.db')
cursor = conn.cursor()

# Check if albums table exists and has data
print('=== TABLES CHECK ===')
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%album%'")
tables = cursor.fetchall()
for t in tables:
    print(f'Table: {t[0]}')
    cursor.execute(f'SELECT COUNT(*) FROM {t[0]}')
    count = cursor.fetchone()[0]
    print(f'  Rows: {count}')

print()

# Albums table analysis
try:
    cursor.execute('SELECT COUNT(*) FROM albums')
    album_count = cursor.fetchone()[0]
    print(f'Total albums in albums table: {album_count}')
    
    cursor.execute('SELECT COUNT(*) FROM albums WHERE cover_url IS NOT NULL')
    with_cover = cursor.fetchone()[0]
    print(f'Albums WITH cover_url: {with_cover}')
    print(f'Albums WITHOUT cover_url: {album_count - with_cover}')
    
    # Sample albums
    print()
    print('=== SAMPLE ALBUMS (first 10) ===')
    cursor.execute('SELECT id, name, artist, cover_url IS NOT NULL, release_date FROM albums LIMIT 10')
    for row in cursor.fetchall():
        print(f'  ID={row[0]}: {row[1]} by {row[2]} | has_cover={row[3]} | date={row[4]}')
    
    # Albums without covers
    print()
    print('=== ALBUMS WITHOUT COVERS (first 10) ===')
    cursor.execute('SELECT id, name, artist FROM albums WHERE cover_url IS NULL LIMIT 10')
    for row in cursor.fetchall():
        print(f'  ID={row[0]}: {row[1]} by {row[2]}')
    
    # Empty albums (no tracks)
    print()
    print('=== ALBUMS WITH NO TRACKS (empty) ===')
    cursor.execute('''
        SELECT a.id, a.name, a.artist 
        FROM albums a
        LEFT JOIN album_tracks at ON a.id = at.album_id
        WHERE at.id IS NULL
        LIMIT 20
    ''')
    empty = cursor.fetchall()
    print(f'Found {len(empty)} empty albums (showing up to 20):')
    for row in empty:
        print(f'  ID={row[0]}: {row[1]} by {row[2]}')

    # Count total empty albums
    cursor.execute('''
        SELECT COUNT(*) 
        FROM albums a
        LEFT JOIN album_tracks at ON a.id = at.album_id
        WHERE at.id IS NULL
    ''')
    empty_count = cursor.fetchone()[0]
    print(f'\nTotal empty albums: {empty_count} / {album_count}')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()

print()

# TrackEnrichment analysis
try:
    print('=== TRACK ENRICHMENTS ===')
    cursor.execute('SELECT COUNT(*) FROM track_enrichments')
    enrichment_count = cursor.fetchone()[0]
    print(f'Total enrichments: {enrichment_count}')
    
    cursor.execute('SELECT COUNT(*) FROM track_enrichments WHERE album_name IS NOT NULL')
    with_album = cursor.fetchone()[0]
    print(f'Enrichments with album_name: {with_album}')
    
    cursor.execute('SELECT COUNT(*) FROM track_enrichments WHERE cover_url IS NOT NULL')
    with_cover = cursor.fetchone()[0]
    print(f'Enrichments with cover_url: {with_cover}')
    
except Exception as e:
    print(f'Error: {e}')

# Album track counts
print()
print('=== ALBUM TRACK DISTRIBUTION ===')
try:
    cursor.execute('''
        SELECT 
            CASE 
                WHEN track_count = 0 THEN '0 tracks'
                WHEN track_count = 1 THEN '1 track'
                WHEN track_count BETWEEN 2 AND 4 THEN '2-4 tracks'
                WHEN track_count BETWEEN 5 AND 10 THEN '5-10 tracks'
                ELSE '10+ tracks'
            END as bucket,
            COUNT(*) as album_count
        FROM (
            SELECT a.id, COUNT(at.id) as track_count
            FROM albums a
            LEFT JOIN album_tracks at ON a.id = at.album_id
            GROUP BY a.id
        )
        GROUP BY bucket
    ''')
    for row in cursor.fetchall():
        print(f'  {row[0]}: {row[1]} albums')
except Exception as e:
    print(f'Error: {e}')

# Check specific problem albums from screenshots
print()
print('=== SPECIFIC ALBUM CHECKS ===')
try:
    # Cold Visions (from screenshot - 16 tracks but shows correctly)
    cursor.execute("SELECT id, name, artist, cover_url IS NOT NULL FROM albums WHERE name LIKE '%Cold Visions%'")
    for row in cursor.fetchall():
        cursor.execute('SELECT COUNT(*) FROM album_tracks WHERE album_id = ?', (row[0],))
        track_count = cursor.fetchone()[0]
        print(f'Cold Visions: ID={row[0]}, artist={row[2]}, has_cover={row[3]}, tracks={track_count}')
    
    # 333 (from screenshot - shows 0 tracks)
    cursor.execute("SELECT id, name, artist, cover_url IS NOT NULL FROM albums WHERE name = '333'")
    for row in cursor.fetchall():
        cursor.execute('SELECT COUNT(*) FROM album_tracks WHERE album_id = ?', (row[0],))
        track_count = cursor.fetchone()[0]
        print(f'333: ID={row[0]}, artist={row[2]}, has_cover={row[3]}, tracks={track_count}')
    
    # Plastic Surgery (from screenshot - has PS placeholder instead of cover)
    cursor.execute("SELECT id, name, artist, cover_url FROM albums WHERE name LIKE '%Plastic Surgery%'")
    for row in cursor.fetchall():
        cursor.execute('SELECT COUNT(*) FROM album_tracks WHERE album_id = ?', (row[0],))
        track_count = cursor.fetchone()[0]
        print(f'Plastic Surgery: ID={row[0]}, artist={row[2]}, cover_url={row[3][:50] if row[3] else None}..., tracks={track_count}')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()

conn.close()

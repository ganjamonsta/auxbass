#!/usr/bin/env python3
"""
Merge duplicate albums (v2 - for Album model).

Finds albums with same name (case-insensitive) and merges them:
- Keeps the album with more tracks/data
- Moves all tracks from duplicate albums to the main one
- Deletes empty duplicates
"""
import sqlite3
from collections import defaultdict

def main():
    conn = sqlite3.connect('tg_player.db')
    c = conn.cursor()
    
    # Find potential duplicates by normalized name
    c.execute('''
        SELECT id, name, artist, cover_url, deezer_album_id, release_date, full_tracklist
        FROM albums
        ORDER BY LOWER(name), id
    ''')
    albums = c.fetchall()
    
    # Group by normalized name
    groups = defaultdict(list)
    for album in albums:
        key = album[1].lower().strip()  # name normalized
        groups[key].append(album)
    
    duplicates_found = 0
    tracks_moved = 0
    albums_deleted = 0
    
    for name, album_list in groups.items():
        if len(album_list) < 2:
            continue
        
        duplicates_found += 1
        print(f"\n=== Duplicate: '{name}' ({len(album_list)} albums) ===")
        
        # Score each album - prefer one with most data
        def score_album(a):
            album_id, name, artist, cover_url, deezer_album_id, release_date, full_tracklist = a
            s = 0
            if cover_url: s += 10
            if deezer_album_id: s += 20
            if release_date: s += 5
            if full_tracklist: s += 15
            # Get track count
            c.execute('SELECT COUNT(*) FROM album_tracks WHERE album_id = ?', (album_id,))
            s += c.fetchone()[0] * 2  # 2 points per track
            return s
        
        scored = [(a, score_album(a)) for a in album_list]
        scored.sort(key=lambda x: -x[1])  # Highest score first
        
        primary = scored[0][0]
        primary_id = primary[0]
        print(f"  Primary: ID={primary_id}, artist='{primary[2]}', score={scored[0][1]}")
        
        for album, score in scored[1:]:
            dup_id = album[0]
            print(f"  Duplicate: ID={dup_id}, artist='{album[2]}', score={score}")
            
            # Move tracks from duplicate to primary
            c.execute('SELECT track_id, track_number FROM album_tracks WHERE album_id = ?', (dup_id,))
            dup_tracks = c.fetchall()
            
            for track_id, track_number in dup_tracks:
                # Check if already in primary
                c.execute('SELECT id FROM album_tracks WHERE album_id = ? AND track_id = ?', 
                         (primary_id, track_id))
                if c.fetchone():
                    print(f"    Track {track_id} already in primary, deleting duplicate link")
                    c.execute('DELETE FROM album_tracks WHERE album_id = ? AND track_id = ?', 
                             (dup_id, track_id))
                else:
                    print(f"    Moving track {track_id} to primary")
                    c.execute('UPDATE album_tracks SET album_id = ? WHERE album_id = ? AND track_id = ?',
                             (primary_id, dup_id, track_id))
                    tracks_moved += 1
            
            # Update primary with any missing data from duplicate
            if not primary[3] and album[3]:  # cover_url
                c.execute('UPDATE albums SET cover_url = ? WHERE id = ?', (album[3], primary_id))
                print(f"    Copied cover_url from duplicate")
            if not primary[4] and album[4]:  # deezer_album_id
                c.execute('UPDATE albums SET deezer_album_id = ? WHERE id = ?', (album[4], primary_id))
                print(f"    Copied deezer_album_id from duplicate")
            if not primary[5] and album[5]:  # release_date
                c.execute('UPDATE albums SET release_date = ? WHERE id = ?', (album[5], primary_id))
                print(f"    Copied release_date from duplicate")
            if not primary[6] and album[6]:  # full_tracklist
                c.execute('UPDATE albums SET full_tracklist = ? WHERE id = ?', (album[6], primary_id))
                print(f"    Copied full_tracklist from duplicate")
            
            # Delete empty duplicate
            c.execute('DELETE FROM albums WHERE id = ?', (dup_id,))
            albums_deleted += 1
            print(f"    Deleted duplicate album ID={dup_id}")
    
    conn.commit()
    conn.close()
    
    print(f"\n=== Summary ===")
    print(f"Duplicate groups found: {duplicates_found}")
    print(f"Tracks moved: {tracks_moved}")
    print(f"Albums deleted: {albums_deleted}")

if __name__ == "__main__":
    main()

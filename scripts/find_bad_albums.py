#!/usr/bin/env python3
"""
Find all albums with track that have no title (Без названия)
"""
import sqlite3
from pathlib import Path

def find_problematic_albums():
    """Find albums containing tracks without titles"""
    
    db_files = list(Path('.').glob('*.db'))
    if not db_files:
        print('❌ No SQLite database files found')
        return
    
    db_file = db_files[0]
    print(f'Scanning database: {db_file}\n')
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Find all albums with tracks that have no title or placeholder title
    cursor.execute("""
        SELECT DISTINCT a.id, a.name, a.artist, COUNT(t.id) as unknown_count
        FROM albums a
        JOIN album_tracks at ON a.id = at.album_id
        JOIN tracks t ON at.track_id = t.id
        WHERE t.title IS NULL OR t.title = '' OR t.title = 'Без названия'
        GROUP BY a.id, a.name, a.artist
        ORDER BY unknown_count DESC
    """)
    
    problematic = cursor.fetchall()
    
    if not problematic:
        print('✅ NO PROBLEMATIC ALBUMS FOUND')
        print('   All albums have proper track titles')
    else:
        print(f'⚠️  FOUND {len(problematic)} albums with tracks without titles:\n')
        
        for album_id, name, artist, unknown_count in problematic:
            print(f'📌 "{name}" by "{artist}"')
            print(f'   ID: {album_id}')
            print(f'   Tracks without title: {unknown_count}')
            
            # Get all tracks in this album
            cursor.execute("""
                SELECT t.id, t.title, t.artist
                FROM album_tracks at
                JOIN tracks t ON at.track_id = t.id
                WHERE at.album_id = ?
                ORDER BY at.track_number
            """, (album_id,))
            
            tracks = cursor.fetchall()
            print(f'   Total tracks in album: {len(tracks)}')
            
            for track_id, title, track_artist in tracks:
                title_display = f'"{title}"' if title and title != 'Без названия' else '[UNKNOWN]'
                artist_display = f'by "{track_artist}"' if track_artist else '[NO ARTIST]'
                print(f'     - Track {track_id}: {title_display} {artist_display}')
            
            print()
    
    conn.close()


if __name__ == '__main__':
    find_problematic_albums()

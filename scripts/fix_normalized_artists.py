#!/usr/bin/env python3
"""
Fix normalized_artist field in albums table.
Re-calculates using updated normalization logic.
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.matching import normalize_artist

# Clear LRU cache to use fresh function
normalize_artist.cache_clear()

def main():
    conn = sqlite3.connect('tg_player.db')
    c = conn.cursor()
    
    # Get all albums
    c.execute('SELECT id, artist, normalized_artist FROM albums')
    albums = c.fetchall()
    
    updated = 0
    for album_id, artist, current_normalized in albums:
        new_normalized = normalize_artist(artist or "")
        
        if new_normalized != current_normalized:
            print(f"Album {album_id}: '{artist}' -> '{new_normalized}' (was: '{current_normalized}')")
            c.execute('UPDATE albums SET normalized_artist = ? WHERE id = ?', 
                     (new_normalized, album_id))
            updated += 1
    
    conn.commit()
    conn.close()
    
    print(f"\nUpdated {updated} albums")

if __name__ == "__main__":
    main()

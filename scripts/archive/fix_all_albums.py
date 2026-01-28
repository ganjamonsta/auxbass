#!/usr/bin/env python3
"""
FULL FIX: Remove ALL wrongly assigned album tracks.

For each track in album_tracks:
- If track has enrichment with deezer_album_id -> check it matches album's deezer_album_id
- If track has enrichment with album_name -> check it matches album name (fuzzy)
- Remove track from album if it doesn't belong
"""
import sqlite3
from difflib import SequenceMatcher

def normalize(s):
    """Normalize string for comparison"""
    if not s:
        return ""
    s = s.lower().strip()
    # Remove common suffixes
    for suffix in [' [explicit]', ' (explicit)', ' (deluxe)', ' (deluxe edition)', 
                   ' (remastered)', ' (remaster)', ' (bonus track version)']:
        s = s.replace(suffix, '')
    return s.strip()

def albums_match(album1, album2):
    """Check if two album names refer to the same album"""
    if not album1 or not album2:
        return False
    
    a1 = normalize(album1)
    a2 = normalize(album2)
    
    if a1 == a2:
        return True
    
    # One contains the other
    if a1 in a2 or a2 in a1:
        return True
    
    # Fuzzy match
    ratio = SequenceMatcher(None, a1, a2).ratio()
    return ratio >= 0.85

conn = sqlite3.connect('tg_player.db')
c = conn.cursor()

# Get ALL album_tracks with enrichment info
c.execute('''
    SELECT at.id, at.album_id, at.track_id, 
           t.title, t.artist,
           a.name as album_name, a.deezer_album_id as album_deezer_id,
           e.album_name as enrich_album, e.deezer_album_id as enrich_deezer_id
    FROM album_tracks at
    JOIN tracks t ON t.id = at.track_id
    JOIN albums a ON a.id = at.album_id
    LEFT JOIN track_enrichments e ON e.track_id = t.id
''')
rows = c.fetchall()

print(f"Checking {len(rows)} album-track associations...")

wrong = []
for row in rows:
    at_id, album_id, track_id, title, artist, album_name, album_deezer, enrich_album, enrich_deezer = row
    
    # If both have deezer_album_id - must match exactly
    if album_deezer and enrich_deezer:
        if album_deezer != enrich_deezer:
            wrong.append((at_id, title, album_name, enrich_album, "deezer_id mismatch"))
            continue
    
    # If enrichment has album_name - check fuzzy match
    if enrich_album:
        if not albums_match(album_name, enrich_album):
            wrong.append((at_id, title, album_name, enrich_album, "name mismatch"))
            continue

print(f"\nFound {len(wrong)} wrongly assigned tracks:")
for at_id, title, album_name, enrich_album, reason in wrong:
    print(f'  "{title}" in "{album_name}" -> should be "{enrich_album}" ({reason})')

if wrong:
    print(f"\nRemoving {len(wrong)} wrong associations...")
    for at_id, _, _, _, _ in wrong:
        c.execute('DELETE FROM album_tracks WHERE id = ?', (at_id,))
    conn.commit()
    print("Done!")
else:
    print("All tracks correctly assigned.")

conn.close()

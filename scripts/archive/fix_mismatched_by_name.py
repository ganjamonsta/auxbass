#!/usr/bin/env python3
"""
Find and fix mismatched album tracks by album name.

For albums without deezer_album_id, checks if track's enrichment album_name
matches the album name.
"""
import sqlite3
from difflib import SequenceMatcher

def similar(a, b):
    """Check if two strings are similar enough"""
    if not a or not b:
        return False
    a, b = a.lower().strip(), b.lower().strip()
    if a == b:
        return True
    # Check ratio
    ratio = SequenceMatcher(None, a, b).ratio()
    return ratio >= 0.8

conn = sqlite3.connect('tg_player.db')
c = conn.cursor()

# Find tracks in albums without deezer_album_id where enrichment album_name doesn't match
c.execute('''
    SELECT at.id, t.id, t.title, a.id, a.name, e.album_name
    FROM album_tracks at
    JOIN tracks t ON t.id = at.track_id
    JOIN albums a ON a.id = at.album_id
    LEFT JOIN track_enrichments e ON e.track_id = t.id
    WHERE a.deezer_album_id IS NULL 
      AND e.album_name IS NOT NULL
''')
rows = c.fetchall()

mismatched = []
for r in rows:
    at_id, t_id, title, a_id, album_name, enrich_album = r
    if not similar(album_name, enrich_album):
        mismatched.append((at_id, title, album_name, enrich_album))

print(f'Checked {len(rows)} tracks, found {len(mismatched)} mismatched:')
for at_id, title, album_name, enrich_album in mismatched[:30]:
    print(f'  "{title}" in "{album_name}" -> should be "{enrich_album}"')

if len(mismatched) > 30:
    print(f'  ... and {len(mismatched) - 30} more')

if mismatched:
    confirm = input(f'\nRemove {len(mismatched)} wrong associations? (y/n): ')
    if confirm.lower() == 'y':
        for at_id, _, _, _ in mismatched:
            c.execute('DELETE FROM album_tracks WHERE id = ?', (at_id,))
        conn.commit()
        print('Done!')
    else:
        print('Cancelled')
else:
    print('All tracks are correctly assigned.')

conn.close()

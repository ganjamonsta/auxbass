#!/usr/bin/env python3
"""
Find and fix mismatched album tracks.

Checks each track against its enrichment data (deezer_album_id)
and removes tracks that don't belong to the album.
"""
import sqlite3

conn = sqlite3.connect('tg_player.db')
c = conn.cursor()

# Find tracks where album's deezer_album_id doesn't match track's enrichment deezer_album_id
c.execute('''
    SELECT at.id, t.id, t.title, a.id, a.name, a.deezer_album_id, 
           e.deezer_album_id, e.album_name
    FROM album_tracks at
    JOIN tracks t ON t.id = at.track_id
    JOIN albums a ON a.id = at.album_id
    LEFT JOIN track_enrichments e ON e.track_id = t.id
    WHERE a.deezer_album_id IS NOT NULL 
      AND e.deezer_album_id IS NOT NULL 
      AND a.deezer_album_id != e.deezer_album_id
''')
rows = c.fetchall()

print(f'Found {len(rows)} mismatched tracks:')
for r in rows:
    at_id, t_id, title, a_id, album_name, album_deezer, track_deezer, enrich_album = r
    print(f'  "{title}" in "{album_name}" (deezer:{album_deezer}) -> should be "{enrich_album}" (deezer:{track_deezer})')

if rows:
    print(f'\nRemoving {len(rows)} wrong associations...')
    for r in rows:
        c.execute('DELETE FROM album_tracks WHERE id = ?', (r[0],))
    conn.commit()
    print('Done!')
else:
    print('All tracks are correctly assigned.')

conn.close()

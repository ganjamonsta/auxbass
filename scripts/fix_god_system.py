#!/usr/bin/env python3
"""Add missing tracks to GOD SYSTEM album"""
import sqlite3

conn = sqlite3.connect('tg_player.db')
c = conn.cursor()

# Track IDs to add to album 20 (GOD SYSTEM)
# DANCE LIKE U IN PAIN, GOD SYSTEM, SHOW OFF
tracks_to_add = [708, 713, 670]

for track_id in tracks_to_add:
    # Check if already in album
    c.execute('SELECT id FROM album_tracks WHERE album_id = 20 AND track_id = ?', (track_id,))
    if not c.fetchone():
        c.execute('INSERT INTO album_tracks (album_id, track_id, track_number) VALUES (20, ?, 0)', (track_id,))
        print(f'Added track {track_id} to album 20')
    else:
        print(f'Track {track_id} already in album')

# Update enrichment for these tracks
for track_id in tracks_to_add:
    c.execute('UPDATE track_enrichments SET album_name = "GOD SYSTEM" WHERE track_id = ?', (track_id,))
    if c.rowcount == 0:
        # Insert if not exists
        c.execute('INSERT INTO track_enrichments (track_id, album_name) VALUES (?, "GOD SYSTEM")', (track_id,))
        print(f'Created enrichment for track {track_id}')
    else:
        print(f'Updated enrichment for track {track_id}')

conn.commit()
conn.close()
print('Done!')

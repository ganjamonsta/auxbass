#!/usr/bin/env python3
import sqlite3
import json

conn = sqlite3.connect('tg_player.db')
c = conn.cursor()

# Check albums with full_tracklist
c.execute('SELECT COUNT(*) FROM albums WHERE full_tracklist IS NOT NULL')
print(f'Albums with full_tracklist: {c.fetchone()[0]}')

c.execute('SELECT COUNT(*) FROM albums')
print(f'Total albums: {c.fetchone()[0]}')

# Sample one album
c.execute('SELECT name, artist, full_tracklist FROM albums WHERE full_tracklist IS NOT NULL LIMIT 1')
row = c.fetchone()
if row:
    tl = json.loads(row[2])
    print(f'\nSample: {row[0]} by {row[1]}')
    print(f'Tracks: {len(tl)}')
    for t in tl[:5]:
        print(f'  {t["track_number"]}. {t["title"]} ({t["duration"]}s)')
    if len(tl) > 5:
        print(f'  ... and {len(tl)-5} more')

# Check albums with 2+ tracks in library
c.execute('''
    SELECT a.name, a.artist, COUNT(at.id) as track_count
    FROM albums a
    LEFT JOIN album_tracks at ON at.album_id = a.id
    GROUP BY a.id
    HAVING track_count >= 2
    ORDER BY track_count DESC
    LIMIT 10
''')
print(f'\nTop albums with 2+ tracks in library:')
for row in c.fetchall():
    print(f'  {row[2]} tracks: {row[0]} by {row[1]}')

conn.close()

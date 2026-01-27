#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('tg_player.db')
c = conn.cursor()

# Get track in album 697
c.execute('''
    SELECT at.track_id, t.title, t.artist
    FROM album_tracks at
    JOIN tracks t ON t.id = at.track_id
    WHERE at.album_id = 697
''')
print('Tracks in album 697:')
for r in c.fetchall():
    print(f'  Track ID={r[0]}: {r[1]} by {r[2]}')

# Check if this track is in user library (for user 874295897)
c.execute('''
    SELECT at.track_id, ul.user_id
    FROM album_tracks at
    LEFT JOIN user_library ul ON ul.track_id = at.track_id
    WHERE at.album_id = 697
''')
print('\nUser library status:')
for r in c.fetchall():
    print(f'  Track ID={r[0]}, User={r[1]}')

# Also check album 13
c.execute('''
    SELECT at.track_id, t.title, COUNT(ul.id) as lib_count
    FROM album_tracks at
    JOIN tracks t ON t.id = at.track_id
    LEFT JOIN user_library ul ON ul.track_id = at.track_id
    WHERE at.album_id = 13
    GROUP BY at.track_id
''')
print('\nTracks in album 13 (with library count):')
for r in c.fetchall():
    print(f'  Track ID={r[0]}: {r[1]} - in {r[2]} libraries')

conn.close()

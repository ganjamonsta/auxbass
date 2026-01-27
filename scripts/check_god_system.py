#!/usr/bin/env python3
"""Check GOD SYSTEM album"""
import sqlite3
import requests
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.config import Settings
settings = Settings()

conn = sqlite3.connect('tg_player.db')
c = conn.cursor()

# Get album info
c.execute('SELECT id, name, artist, cover_url, deezer_album_id FROM albums WHERE id = 20')
r = c.fetchone()
print(f"=== Album {r[0]}: {r[1]} by {r[2]} ===")
print(f"Cover: {r[3]}")
print(f"Deezer ID: {r[4]}")

# Get tracks in this album
c.execute('''
    SELECT t.id, t.title, t.artist, e.album_name
    FROM album_tracks at
    JOIN tracks t ON t.id = at.track_id
    LEFT JOIN track_enrichments e ON e.track_id = t.id
    WHERE at.album_id = 20
    ORDER BY t.title
''')
album_tracks = c.fetchall()
print(f"\n=== Tracks in album ({len(album_tracks)}) ===")
for t in album_tracks:
    print(f"  {t[1]} by {t[2]} (enrichment: {t[3]})")

# Get ALL Kai Angel tracks in library
c.execute('''
    SELECT t.id, t.title, t.artist, e.album_name, e.deezer_album_id
    FROM tracks t
    LEFT JOIN track_enrichments e ON e.track_id = t.id
    WHERE LOWER(t.artist) LIKE '%kai angel%'
    ORDER BY t.title
''')
all_kai_tracks = c.fetchall()
print(f"\n=== ALL Kai Angel tracks in library ({len(all_kai_tracks)}) ===")
for t in all_kai_tracks:
    print(f"  [{t[0]}] {t[1]} by {t[2]} -> album: {t[3]} (deezer: {t[4]})")

# Check which are NOT in album 20
album_track_ids = {t[0] for t in album_tracks}
missing = [t for t in all_kai_tracks if t[0] not in album_track_ids and t[3] and 'god system' in t[3].lower()]
print(f"\n=== Kai Angel tracks with GOD SYSTEM enrichment but NOT in album ({len(missing)}) ===")
for t in missing:
    print(f"  [{t[0]}] {t[1]} -> {t[3]}")

conn.close()

# Get from Last.fm
print("\n=== Last.fm tracklist for GOD SYSTEM ===")
r = requests.get('https://ws.audioscrobbler.com/2.0/', params={
    'method': 'album.getinfo',
    'artist': 'Kai Angel',
    'album': 'GOD SYSTEM',
    'api_key': settings.lastfm_api_key,
    'format': 'json'
})

data = r.json()
if 'album' in data:
    album = data['album']
    tracks = album.get('tracks', {}).get('track', [])
    if isinstance(tracks, dict):
        tracks = [tracks]
    print(f"Total tracks on Last.fm: {len(tracks)}")
    for i, t in enumerate(tracks, 1):
        print(f"  {i}. {t.get('name')}")
else:
    print(f"Error: {data}")

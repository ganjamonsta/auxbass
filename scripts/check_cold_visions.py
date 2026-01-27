#!/usr/bin/env python3
"""Check Cold Visions album"""
import sqlite3
import requests
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.config import Settings
settings = Settings()

# Get tracks from DB
conn = sqlite3.connect('tg_player.db')
c = conn.cursor()

c.execute('''
    SELECT t.title, e.album_name, e.deezer_album_id
    FROM album_tracks at
    JOIN tracks t ON t.id = at.track_id
    LEFT JOIN track_enrichments e ON e.track_id = t.id
    WHERE at.album_id = 17
    ORDER BY at.track_number
''')
db_tracks = c.fetchall()
conn.close()

print("=== Tracks in DB (album 17 - Cold Visions) ===")
for title, enrich_album, deezer_album in db_tracks:
    print(f"  {title} -> enrichment: {enrich_album} (deezer: {deezer_album})")

# Get from Last.fm
print("\n=== Last.fm tracklist for Cold Visions ===")
r = requests.get('https://ws.audioscrobbler.com/2.0/', params={
    'method': 'album.getinfo',
    'artist': 'Bladee',
    'album': 'Cold Visions',
    'api_key': settings.lastfm_api_key,
    'format': 'json'
})

data = r.json()
if 'album' in data:
    album = data['album']
    tracks = album.get('tracks', {}).get('track', [])
    if isinstance(tracks, dict):
        tracks = [tracks]
    
    lastfm_titles = set()
    for i, t in enumerate(tracks, 1):
        name = t.get('name')
        lastfm_titles.add(name.lower())
        print(f"  {i}. {name}")
    
    # Compare
    print("\n=== Comparison ===")
    db_titles = {t[0].lower() for t in db_tracks}
    
    wrong = []
    for title, enrich_album, _ in db_tracks:
        if title.lower() not in lastfm_titles:
            wrong.append(title)
            print(f"  WRONG: '{title}' not in Last.fm tracklist")
    
    missing = lastfm_titles - db_titles
    if missing:
        print(f"\n  Missing from library: {missing}")
    
    if not wrong:
        print("  All tracks correct!")
else:
    print(f"Error: {data}")

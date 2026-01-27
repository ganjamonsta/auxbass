#!/usr/bin/env python3
"""Check Last.fm tracklist for album 333 by Bladee"""
import requests
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.config import Settings
settings = Settings()

r = requests.get('https://ws.audioscrobbler.com/2.0/', params={
    'method': 'album.getinfo',
    'artist': 'Bladee',
    'album': '333',
    'api_key': settings.lastfm_api_key,
    'format': 'json'
})

data = r.json()
if 'album' in data:
    album = data['album']
    print(f"Album: {album.get('name')} by {album.get('artist')}")
    print(f"Tracks:")
    tracks = album.get('tracks', {}).get('track', [])
    if isinstance(tracks, dict):
        tracks = [tracks]
    for i, t in enumerate(tracks, 1):
        print(f"  {i}. {t.get('name')}")
else:
    print("Error:", data)

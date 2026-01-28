#!/usr/bin/env python3
"""Check full Last.fm tracklist for 333"""
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
print("Raw response:")
print(data)

if 'album' in data:
    album = data['album']
    print(f"\n\nAlbum: {album.get('name')} by {album.get('artist')}")
    print(f"Tracks field type: {type(album.get('tracks'))}")
    tracks_data = album.get('tracks', {})
    print(f"Tracks data: {tracks_data}")
    
    tracks = tracks_data.get('track', [])
    if isinstance(tracks, dict):
        tracks = [tracks]
    
    print(f"\nTotal tracks: {len(tracks)}")
    for i, t in enumerate(tracks, 1):
        print(f"  {i}. {t.get('name')}")

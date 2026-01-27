#!/usr/bin/env python3
"""
Rebuild album_tracks assignments based on current enrichment data.

This script:
1. Clears album_tracks for affected albums
2. Re-assigns tracks to albums based on enrichment.album_name
"""
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "tg_player.db"


def rebuild_album_tracks():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("="*60)
    print("REBUILDING ALBUM TRACKS ASSIGNMENTS")
    print("="*60)
    
    # Get all tracks with enrichment album_name
    cursor.execute("""
        SELECT t.id as track_id, t.artist, t.title, e.album_name, e.cover_url
        FROM tracks t
        JOIN track_enrichments e ON t.id = e.track_id
        WHERE e.album_name IS NOT NULL AND e.album_name != ''
    """)
    
    tracks = cursor.fetchall()
    print(f"Found {len(tracks)} tracks with album enrichment")
    
    # Get current album_tracks
    cursor.execute("SELECT track_id, album_id FROM album_tracks")
    current_assignments = {row['track_id']: row['album_id'] for row in cursor.fetchall()}
    
    # Get all albums
    cursor.execute("SELECT id, name, normalized_name, artist FROM albums")
    albums = {row['id']: dict(row) for row in cursor.fetchall()}
    albums_by_norm_name = {}
    for album in albums.values():
        key = album['normalized_name'].lower()
        if key not in albums_by_norm_name:
            albums_by_norm_name[key] = album
    
    changes = []
    new_assignments = []
    
    for track in tracks:
        track_id = track['track_id']
        album_name = track['album_name']
        norm_album = album_name.lower().strip()
        
        # Find album by normalized name
        album = albums_by_norm_name.get(norm_album)
        
        if not album:
            # Try partial match
            for key, a in albums_by_norm_name.items():
                if norm_album in key or key in norm_album:
                    album = a
                    break
        
        if album:
            current_album_id = current_assignments.get(track_id)
            if current_album_id != album['id']:
                changes.append({
                    'track_id': track_id,
                    'artist': track['artist'],
                    'title': track['title'],
                    'old_album_id': current_album_id,
                    'new_album_id': album['id'],
                    'album_name': album['name'],
                    'enrichment_album': album_name,
                })
                new_assignments.append((track_id, album['id']))
    
    print(f"\nFound {len(changes)} tracks needing reassignment")
    
    if changes:
        print("\nChanges to apply:")
        for ch in changes[:20]:  # Show first 20
            old_name = albums.get(ch['old_album_id'], {}).get('name', 'None') if ch['old_album_id'] else 'None'
            print(f"  [{ch['track_id']}] {ch['artist']} - {ch['title']}")
            print(f"      {old_name} -> {ch['album_name']}")
        
        if len(changes) > 20:
            print(f"  ... and {len(changes) - 20} more")
        
        confirm = input("\nApply changes? (y/n): ")
        if confirm.lower() == 'y':
            for track_id, album_id in new_assignments:
                # Delete old assignment
                cursor.execute("DELETE FROM album_tracks WHERE track_id = ?", (track_id,))
                # Insert new assignment
                cursor.execute("""
                    INSERT INTO album_tracks (track_id, album_id, created_at)
                    VALUES (?, ?, ?)
                """, (track_id, album_id, datetime.now().isoformat()))
            
            conn.commit()
            print(f"\nApplied {len(new_assignments)} changes!")
        else:
            print("Cancelled")
    else:
        print("No changes needed")
    
    conn.close()


def show_album_tracks(album_name: str):
    """Show current tracks in an album."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT a.id, a.name, a.artist, COUNT(at.track_id) as track_count
        FROM albums a
        LEFT JOIN album_tracks at ON a.id = at.album_id
        WHERE a.name LIKE ?
        GROUP BY a.id
    """, (f"%{album_name}%",))
    
    albums = cursor.fetchall()
    
    for album in albums:
        print(f"\n{'='*60}")
        print(f"Album: {album['name']} by {album['artist']}")
        print(f"Tracks: {album['track_count']}")
        print('='*60)
        
        cursor.execute("""
            SELECT t.id, t.title, t.artist, e.album_name as enrichment_album
            FROM album_tracks at
            JOIN tracks t ON at.track_id = t.id
            LEFT JOIN track_enrichments e ON t.id = e.track_id
            WHERE at.album_id = ?
            ORDER BY t.title
        """, (album['id'],))
        
        for track in cursor.fetchall():
            marker = ""
            if track['enrichment_album'] and track['enrichment_album'].lower() != album['name'].lower():
                marker = f" *** should be in '{track['enrichment_album']}' ***"
            print(f"  [{track['id']}] {track['artist']} - {track['title']}{marker}")
    
    conn.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--show":
        album_name = sys.argv[2] if len(sys.argv) > 2 else "333"
        show_album_tracks(album_name)
    else:
        rebuild_album_tracks()

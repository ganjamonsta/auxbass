#!/usr/bin/env python3
"""
Re-enrich tracks that have wrong album assignments.
Uses Last.fm as PRIMARY source, Deezer only as fallback.

This script:
1. Finds tracks with suspicious album assignments
2. Re-enriches them using current logic (Last.fm first)
3. Updates track_enrichments with correct data
"""
import asyncio
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.services.metadata import metadata_service

DB_PATH = Path(__file__).parent.parent / "tg_player.db"

# Known problematic albums that need re-enrichment verification
SUSPICIOUS_ALBUMS = [
    "333",  # Many wrong tracks assigned here
]

# Tracks we KNOW are wrong (from Last.fm verification)
KNOWN_WRONG_TRACKS = {
    # track_id: correct_album_from_lastfm (or None if should be removed)
    # These will be fixed regardless
}


async def get_current_enrichment(title: str, artist: str) -> dict:
    """Get fresh enrichment data using current logic (Last.fm first)."""
    return await metadata_service.enrich_track(title, artist)


async def re_enrich_album_tracks(album_name: str, dry_run: bool = True):
    """Re-enrich all tracks assigned to a specific album."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print(f"\n{'='*60}")
    print(f"Re-enriching tracks with album_name = '{album_name}'")
    print(f"{'='*60}")
    
    # Find tracks with this album
    cursor.execute("""
        SELECT t.id, t.title, t.artist, e.album_name, e.id as enrichment_id
        FROM tracks t
        JOIN track_enrichments e ON t.id = e.track_id
        WHERE e.album_name = ?
        ORDER BY t.artist, t.title
    """, (album_name,))
    
    tracks = cursor.fetchall()
    print(f"Found {len(tracks)} tracks with album '{album_name}'")
    
    changes = []
    
    for track in tracks:
        track_id = track['id']
        title = track['title']
        artist = track['artist']
        current_album = track['album_name']
        enrichment_id = track['enrichment_id']
        
        print(f"\n[{track_id}] {artist} - {title}")
        print(f"   Current album: {current_album}")
        
        # Get fresh enrichment
        fresh = await get_current_enrichment(title, artist)
        new_album = fresh.get('album')
        source = fresh.get('source', 'unknown')
        
        print(f"   Fresh enrichment: album='{new_album}' (source: {source})")
        
        if new_album != current_album:
            print(f"   >>> CHANGE NEEDED: '{current_album}' -> '{new_album}'")
            changes.append({
                'track_id': track_id,
                'enrichment_id': enrichment_id,
                'title': title,
                'artist': artist,
                'old_album': current_album,
                'new_album': new_album,
                'new_cover': fresh.get('cover_url'),
                'new_genre': fresh.get('genre'),
                'new_release_date': fresh.get('release_date'),
                'source': source,
            })
        else:
            print(f"   OK - album is correct")
        
        # Rate limit
        await asyncio.sleep(0.3)
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {len(changes)} tracks need album changes")
    print(f"{'='*60}")
    
    if changes:
        for ch in changes:
            print(f"  [{ch['track_id']}] {ch['artist']} - {ch['title']}")
            print(f"      '{ch['old_album']}' -> '{ch['new_album']}'")
    
    if not dry_run and changes:
        print(f"\nApplying {len(changes)} changes...")
        for ch in changes:
            cursor.execute("""
                UPDATE track_enrichments 
                SET album_name = ?,
                    cover_url = COALESCE(?, cover_url),
                    genre = COALESCE(?, genre),
                    release_date = COALESCE(?, release_date),
                    enriched_at = ?
                WHERE id = ?
            """, (
                ch['new_album'],
                ch['new_cover'],
                ch['new_genre'],
                ch['new_release_date'],
                datetime.now().isoformat(),
                ch['enrichment_id'],
            ))
        conn.commit()
        print(f"Applied {len(changes)} changes!")
    elif dry_run and changes:
        print("\n*** DRY RUN - no changes applied. Run with --apply to apply changes ***")
    
    conn.close()
    return changes


async def re_enrich_tracks_without_album(limit: int = 50, dry_run: bool = True):
    """Re-enrich tracks that have enrichment but no album_name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print(f"\n{'='*60}")
    print(f"Re-enriching tracks with missing album_name")
    print(f"{'='*60}")
    
    cursor.execute("""
        SELECT t.id, t.title, t.artist, e.id as enrichment_id
        FROM tracks t
        JOIN track_enrichments e ON t.id = e.track_id
        WHERE (e.album_name IS NULL OR e.album_name = '')
          AND t.enrichment_status = 'completed'
        ORDER BY t.artist, t.title
        LIMIT ?
    """, (limit,))
    
    tracks = cursor.fetchall()
    print(f"Found {len(tracks)} tracks without album (limit {limit})")
    
    changes = []
    
    for track in tracks:
        track_id = track['id']
        title = track['title']
        artist = track['artist']
        enrichment_id = track['enrichment_id']
        
        print(f"\n[{track_id}] {artist} - {title}")
        
        fresh = await get_current_enrichment(title, artist)
        new_album = fresh.get('album')
        source = fresh.get('source', 'unknown')
        
        if new_album:
            print(f"   Found album: '{new_album}' (source: {source})")
            changes.append({
                'track_id': track_id,
                'enrichment_id': enrichment_id,
                'title': title,
                'artist': artist,
                'new_album': new_album,
                'new_cover': fresh.get('cover_url'),
                'new_genre': fresh.get('genre'),
                'new_release_date': fresh.get('release_date'),
                'source': source,
            })
        else:
            print(f"   Still no album found")
        
        await asyncio.sleep(0.3)
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {len(changes)} tracks can get album data")
    print(f"{'='*60}")
    
    if not dry_run and changes:
        print(f"\nApplying {len(changes)} changes...")
        for ch in changes:
            cursor.execute("""
                UPDATE track_enrichments 
                SET album_name = ?,
                    cover_url = COALESCE(?, cover_url),
                    genre = COALESCE(?, genre),
                    release_date = COALESCE(?, release_date),
                    enriched_at = ?
                WHERE id = ?
            """, (
                ch['new_album'],
                ch['new_cover'],
                ch['new_genre'],
                ch['new_release_date'],
                datetime.now().isoformat(),
                ch['enrichment_id'],
            ))
        conn.commit()
        print(f"Applied {len(changes)} changes!")
    elif dry_run and changes:
        print("\n*** DRY RUN - no changes applied. Run with --apply to apply changes ***")
    
    conn.close()
    return changes


async def main():
    import argparse
    parser = argparse.ArgumentParser(description='Re-enrich tracks with wrong album assignments')
    parser.add_argument('--apply', action='store_true', help='Actually apply changes (default is dry run)')
    parser.add_argument('--album', type=str, help='Re-enrich specific album')
    parser.add_argument('--missing', action='store_true', help='Re-enrich tracks with missing album')
    parser.add_argument('--limit', type=int, default=50, help='Limit for missing album re-enrichment')
    args = parser.parse_args()
    
    dry_run = not args.apply
    
    if args.album:
        await re_enrich_album_tracks(args.album, dry_run=dry_run)
    elif args.missing:
        await re_enrich_tracks_without_album(limit=args.limit, dry_run=dry_run)
    else:
        # Default: re-enrich suspicious albums
        for album_name in SUSPICIOUS_ALBUMS:
            await re_enrich_album_tracks(album_name, dry_run=dry_run)


if __name__ == "__main__":
    asyncio.run(main())

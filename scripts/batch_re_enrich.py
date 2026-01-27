#!/usr/bin/env python3
"""
Batch re-enrich tracks using fixed logic (Last.fm first, Deezer fallback).

This script re-enriches tracks that may have wrong album data from old logic.
"""
import asyncio
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.services.metadata import metadata_service

DB_PATH = Path(__file__).parent.parent / "tg_player.db"


async def re_enrich_all_completed(batch_size: int = 20, dry_run: bool = True):
    """
    Re-enrich all completed tracks and compare with current data.
    Only updates if the new data is different.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("="*60)
    print("BATCH RE-ENRICHMENT (Last.fm first, Deezer fallback)")
    print("="*60)
    
    # Get all tracks with enrichment
    cursor.execute("""
        SELECT t.id, t.title, t.artist, e.id as enrichment_id, e.album_name
        FROM tracks t
        JOIN track_enrichments e ON t.id = e.track_id
        WHERE t.enrichment_status = 'completed'
        ORDER BY t.id
    """)
    
    all_tracks = cursor.fetchall()
    print(f"Found {len(all_tracks)} completed tracks")
    
    changes = []
    processed = 0
    
    for i, track in enumerate(all_tracks):
        track_id = track['id']
        title = track['title']
        artist = track['artist']
        current_album = track['album_name']
        enrichment_id = track['enrichment_id']
        
        # Get fresh enrichment
        fresh = await metadata_service.enrich_track(title, artist)
        new_album = fresh.get('album')
        source = fresh.get('source', 'unknown')
        
        # Compare
        if new_album != current_album:
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
            print(f"[{track_id}] {artist} - {title}: '{current_album}' -> '{new_album}' ({source})")
        
        processed += 1
        
        # Progress
        if processed % 50 == 0:
            print(f"Processed {processed}/{len(all_tracks)}, changes: {len(changes)}")
        
        # Rate limit - 4 requests per second
        await asyncio.sleep(0.25)
        
        # Stop after batch_size for testing
        if batch_size and processed >= batch_size:
            print(f"\nStopped after {batch_size} tracks (use --all for full run)")
            break
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {len(changes)} tracks need album changes out of {processed} processed")
    print(f"{'='*60}")
    
    if changes and not dry_run:
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
    elif changes and dry_run:
        print("\n*** DRY RUN - no changes applied. Use --apply to apply changes ***")
    
    conn.close()
    
    # Close aiohttp session
    await metadata_service.close()
    
    return changes


async def main():
    import argparse
    parser = argparse.ArgumentParser(description='Batch re-enrich tracks with correct Last.fm/Deezer logic')
    parser.add_argument('--apply', action='store_true', help='Actually apply changes (default is dry run)')
    parser.add_argument('--all', action='store_true', help='Process all tracks (default: first 20)')
    parser.add_argument('--batch', type=int, default=20, help='Batch size (default: 20)')
    args = parser.parse_args()
    
    batch_size = None if args.all else args.batch
    dry_run = not args.apply
    
    await re_enrich_all_completed(batch_size=batch_size, dry_run=dry_run)


if __name__ == "__main__":
    asyncio.run(main())

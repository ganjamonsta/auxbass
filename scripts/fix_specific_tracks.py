#!/usr/bin/env python3
"""
Fix specific tracks with incorrect album assignments from Deezer.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, delete
from shared.database import get_session
from shared.models import Track, Playlist, PlaylistTrack
from bot.services.albums import album_service


# Tracks to fix: (track_id, correct_album, correct_deezer_album_id or None)
FIXES = [
    # D.O.A should be in Cold Visions, not EXETER
    (871, "Cold Visions", None),
    
    # BE NICE TO ME is from "Icedancer" by Bladee  
    (281, "Icedancer", None),
    
    # "bladee - Insect" - this looks like a malformed title, probably should be just "Insect"
    # It's from "Gluee" album
    (583, "Gluee", None),
]

# Playlists to delete (wrong albums that shouldn't exist)
PLAYLISTS_TO_DELETE = [
    676,  # Rolling 200 Deep - not a Bladee album
]


async def fix_tracks():
    """Fix incorrect track metadata and rebuild albums."""
    
    async with get_session() as session:
        print("=== Fixing track metadata ===")
        
        for track_id, correct_album, correct_deezer_id in FIXES:
            track = await session.get(Track, track_id)
            if not track:
                print(f"  Track {track_id} not found, skipping")
                continue
            
            old_album = track.album
            old_deezer_id = track.deezer_album_id
            
            track.album = correct_album
            track.deezer_album_id = correct_deezer_id
            
            print(f"  Track {track_id} '{track.title}':")
            print(f"    album: '{old_album}' -> '{correct_album}'")
            print(f"    deezer_album_id: {old_deezer_id} -> {correct_deezer_id}")
        
        await session.commit()
        print("  ✓ Track metadata updated")
        
        # Delete wrong playlists
        print("\n=== Deleting incorrect playlists ===")
        for pl_id in PLAYLISTS_TO_DELETE:
            playlist = await session.get(Playlist, pl_id)
            if playlist:
                # First delete playlist tracks
                await session.execute(
                    delete(PlaylistTrack).where(PlaylistTrack.playlist_id == pl_id)
                )
                await session.delete(playlist)
                print(f"  Deleted playlist {pl_id}: '{playlist.name}'")
            else:
                print(f"  Playlist {pl_id} not found, skipping")
        
        await session.commit()
        print("  ✓ Playlists deleted")
    
    # Get affected user IDs and rebuild their albums
    print("\n=== Rebuilding albums ===")
    
    async with get_session() as session:
        # Get user IDs for affected tracks
        result = await session.execute(
            select(Track.user_id).where(Track.id.in_([t[0] for t in FIXES])).distinct()
        )
        user_ids = [row[0] for row in result.all()]
    
    for user_id in user_ids:
        print(f"\nRebuilding albums for user {user_id}...")
        try:
            stats = await album_service.assemble_albums_for_user(user_id)
            print(f"  Created: {stats.get('created', 0)}, Updated: {stats.get('updated', 0)}, "
                  f"Merged: {stats.get('merged', 0)}, Cleaned: {stats.get('cleaned', 0)}")
        except Exception as e:
            print(f"  Error: {e}")


if __name__ == "__main__":
    print("Fix Incorrect Album Assignments")
    print("="*50)
    asyncio.run(fix_tracks())
    print("\nDone!")

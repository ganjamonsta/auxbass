#!/usr/bin/env python3
"""
Fix incorrect album assignments.

This script:
1. Clears all auto-album playlists (removes PlaylistTrack entries, not playlists themselves)
2. Rebuilds album playlists with correct artist matching logic

Run this after deploying the fixed get_album_tracks function.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, delete, func
from shared.database import get_session
from shared.models import Playlist, PlaylistTrack, UserLibrary
from bot.services.albums import album_service


async def fix_album_assignments():
    """Clear and rebuild all auto-album playlists."""
    
    async with get_session() as session:
        # Get all users with auto-albums
        result = await session.execute(
            select(Playlist.user_id)
            .where(Playlist.is_auto_album == True)
            .distinct()
        )
        user_ids = [row[0] for row in result.all()]
        print(f"Found {len(user_ids)} users with auto-albums")
        
        # Get stats before cleanup
        total_albums = await session.scalar(
            select(func.count(Playlist.id))
            .where(Playlist.is_auto_album == True)
        )
        print(f"Total auto-albums: {total_albums}")
        
        # Clear all playlist_track entries for auto-albums
        # This keeps the playlists but removes track assignments
        result = await session.execute(
            select(Playlist.id)
            .where(Playlist.is_auto_album == True)
        )
        album_ids = [row[0] for row in result.all()]
        
        if album_ids:
            deleted = await session.execute(
                delete(PlaylistTrack)
                .where(PlaylistTrack.playlist_id.in_(album_ids))
            )
            await session.commit()
            print(f"Cleared {deleted.rowcount} track assignments from {len(album_ids)} albums")
    
    # Rebuild albums for each user
    total_stats = {
        "users_processed": 0,
        "albums_updated": 0,
        "albums_created": 0,
        "albums_merged": 0,
        "albums_cleaned": 0,
    }
    
    for user_id in user_ids:
        try:
            print(f"\nRebuilding albums for user {user_id}...")
            stats = await album_service.assemble_albums_for_user(user_id)
            
            total_stats["users_processed"] += 1
            total_stats["albums_updated"] += stats.get("updated", 0)
            total_stats["albums_created"] += stats.get("created", 0)
            total_stats["albums_merged"] += stats.get("merged", 0)
            total_stats["albums_cleaned"] += stats.get("cleaned", 0)
            
            print(f"  Created: {stats.get('created', 0)}, Updated: {stats.get('updated', 0)}, "
                  f"Merged: {stats.get('merged', 0)}, Cleaned: {stats.get('cleaned', 0)}")
            
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"  Users processed: {total_stats['users_processed']}")
    print(f"  Albums created: {total_stats['albums_created']}")
    print(f"  Albums updated: {total_stats['albums_updated']}")
    print(f"  Albums merged: {total_stats['albums_merged']}")
    print(f"  Albums cleaned: {total_stats['albums_cleaned']}")


if __name__ == "__main__":
    print("Album Assignment Fix Script")
    print("="*50)
    print("This will rebuild all auto-album playlists with correct artist matching.")
    print()
    
    asyncio.run(fix_album_assignments())
    print("\nDone!")

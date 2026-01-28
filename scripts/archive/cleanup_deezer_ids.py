#!/usr/bin/env python3
"""
Clean up all deezer_album_id from tracks and rebuild albums.
This switches to Last.fm-based album grouping (by album name only).
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update, delete, func
from shared.database import get_session
from shared.models import Track, Playlist, PlaylistTrack, UserLibrary
from bot.services.albums import album_service


async def cleanup_and_rebuild():
    """Remove all deezer_album_id and rebuild albums."""
    
    async with get_session() as session:
        # Count tracks with deezer_album_id
        count = await session.scalar(
            select(func.count(Track.id))
            .where(Track.deezer_album_id.isnot(None))
        )
        print(f"Found {count} tracks with deezer_album_id")
        
        # Clear all deezer_album_id
        if count > 0:
            await session.execute(
                update(Track).values(deezer_album_id=None)
            )
            await session.commit()
            print(f"✓ Cleared deezer_album_id from all tracks")
        
        # Also clear deezer_album_id from playlists
        pl_count = await session.scalar(
            select(func.count(Playlist.id))
            .where(Playlist.deezer_album_id.isnot(None))
        )
        if pl_count > 0:
            await session.execute(
                update(Playlist).values(deezer_album_id=None)
            )
            await session.commit()
            print(f"✓ Cleared deezer_album_id from {pl_count} playlists")
        
        # Get all users with auto-albums
        result = await session.execute(
            select(Playlist.user_id)
            .where(Playlist.is_auto_album == True)
            .distinct()
        )
        user_ids = [row[0] for row in result.all()]
        print(f"\nFound {len(user_ids)} users with auto-albums")
        
        # Clear all playlist tracks from auto-albums
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
            print(f"✓ Cleared {deleted.rowcount} track assignments from {len(album_ids)} albums")
    
    # Rebuild albums for each user
    print("\n=== Rebuilding albums ===")
    total_stats = {
        "users": 0,
        "created": 0,
        "updated": 0,
        "merged": 0,
        "cleaned": 0,
    }
    
    for user_id in user_ids:
        try:
            stats = await album_service.assemble_albums_for_user(user_id)
            total_stats["users"] += 1
            total_stats["created"] += stats.get("created", 0)
            total_stats["updated"] += stats.get("updated", 0)
            total_stats["merged"] += stats.get("merged", 0)
            total_stats["cleaned"] += stats.get("cleaned", 0)
            print(f"  User {user_id}: created={stats.get('created', 0)}, merged={stats.get('merged', 0)}, cleaned={stats.get('cleaned', 0)}")
        except Exception as e:
            print(f"  User {user_id}: ERROR - {e}")
    
    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"  Users processed: {total_stats['users']}")
    print(f"  Albums created: {total_stats['created']}")
    print(f"  Albums updated: {total_stats['updated']}")
    print(f"  Albums merged: {total_stats['merged']}")
    print(f"  Albums cleaned: {total_stats['cleaned']}")


if __name__ == "__main__":
    print("Deezer Album ID Cleanup Script")
    print("="*50)
    print("This will remove all deezer_album_id and rebuild albums")
    print("using album name + artist matching (Last.fm style).")
    print()
    
    asyncio.run(cleanup_and_rebuild())
    print("\nDone!")

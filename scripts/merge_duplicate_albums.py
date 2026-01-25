#!/usr/bin/env python3
"""
Merge duplicate album playlists.

This script finds and merges duplicate auto-album playlists that exist due to:
- Different album name spellings (D&G vs D & G)
- Some tracks having deezer_album_id, others not
- Different artist capitalization (BLADEE vs Bladee)

After running this script, the improved album grouping logic will prevent
future duplicates from being created.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from shared.database import get_session
from shared.models import Playlist, PlaylistTrack, User
from bot.services.albums import album_service, normalize_album_name


async def find_all_users_with_albums() -> list[int]:
    """Get all user IDs that have auto-album playlists."""
    async with get_session() as session:
        result = await session.execute(
            select(Playlist.user_id)
            .where(Playlist.is_auto_album == True)
            .distinct()
        )
        return [row[0] for row in result.all()]


async def analyze_duplicates(user_id: int) -> list[list[dict]]:
    """
    Analyze duplicate album playlists for a user.
    Returns groups of duplicates with their info.
    """
    async with get_session() as session:
        result = await session.execute(
            select(Playlist)
            .where(
                Playlist.user_id == user_id,
                Playlist.is_auto_album == True
            )
        )
        playlists = list(result.scalars().all())
        
        # Get track counts for each playlist
        playlist_info = []
        for pl in playlists:
            track_count = await session.scalar(
                select(func.count(PlaylistTrack.id))
                .where(PlaylistTrack.playlist_id == pl.id)
            ) or 0
            
            playlist_info.append({
                "id": pl.id,
                "name": pl.name,
                "album_artist": pl.album_artist,
                "deezer_album_id": pl.deezer_album_id,
                "cover_url": pl.cover_url,
                "track_count": track_count,
                "album_norm": normalize_album_name(pl.name) if pl.name else "",
                "playlist": pl
            })
        
        # Group by normalized album name and deezer_album_id
        groups: dict[str, list] = {}
        
        for info in playlist_info:
            if info["deezer_album_id"]:
                key = f"deezer:{info['deezer_album_id']}"
            else:
                key = f"album:{info['album_norm']}"
            
            if key not in groups:
                groups[key] = []
            groups[key].append(info)
        
        # Return only groups with duplicates
        return [g for g in groups.values() if len(g) > 1]


async def main():
    print("=" * 70)
    print("MERGE DUPLICATE ALBUM PLAYLISTS")
    print("=" * 70)
    
    # Get all users with albums
    print("\n1. Finding users with auto-albums...")
    user_ids = await find_all_users_with_albums()
    print(f"   Found {len(user_ids)} users with auto-album playlists")
    
    total_duplicates = 0
    all_duplicate_groups = []
    
    # Analyze each user
    print("\n2. Analyzing duplicates...")
    for user_id in user_ids:
        duplicates = await analyze_duplicates(user_id)
        if duplicates:
            all_duplicate_groups.append((user_id, duplicates))
            for group in duplicates:
                total_duplicates += len(group) - 1  # Count extras, not the survivor
    
    if total_duplicates == 0:
        print("\n✓ No duplicate album playlists found!")
        return
    
    # Show duplicates
    print(f"\n   Found {total_duplicates} duplicate playlists to merge:\n")
    
    for user_id, groups in all_duplicate_groups:
        print(f"   User {user_id}:")
        for group in groups:
            print(f"      Group (will merge into 1):")
            for info in group:
                deezer = f" [deezer:{info['deezer_album_id']}]" if info['deezer_album_id'] else ""
                cover = " 🖼️" if info['cover_url'] else ""
                print(f"         - [{info['id']}] {info['name']} ({info['track_count']} tracks){deezer}{cover}")
            print()
    
    # Confirm
    confirm = input("Proceed with merge? [y/N]: ").strip().lower()
    if confirm != 'y':
        print("Aborted.")
        return
    
    # Execute merges
    print("\n3. Merging duplicates...")
    merged_count = 0
    
    for user_id, groups in all_duplicate_groups:
        for group in groups:
            playlists = [info["playlist"] for info in group]
            try:
                survivor = await album_service.merge_duplicate_playlists(playlists)
                if survivor:
                    merged_count += len(group) - 1
                    print(f"   ✓ Merged {len(group)} playlists into '{survivor.name}'")
            except Exception as e:
                print(f"   ✗ Error merging group: {e}")
    
    print("\n" + "=" * 70)
    print(f"DONE! Merged {merged_count} duplicate playlists.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

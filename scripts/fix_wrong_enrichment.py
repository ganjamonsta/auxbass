#!/usr/bin/env python3
"""
Fix tracks with wrong enrichment data.
This script resets enrichment for tracks that were incorrectly matched
to albums/artists on Deezer due to the "first result fallback" bug.

The bug caused tracks like:
- Bladee "Flatline" -> blanke "FLATLINE" 
- Bladee "LUCKY LUKE" -> Lucky Luke cartoon soundtrack
- Bladee "SAD MEAL" -> Jok'Chirac "Jok'Chirac"

This script:
1. Finds tracks where album name = track title (likely wrong singles)
2. Finds tracks with suspicious album names (known bad patterns)
3. Resets their enrichment status to "pending" for re-processing
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update, func
from shared.database import get_session
from shared.models import Track, Playlist, PlaylistTrack


# Known bad album patterns that indicate wrong enrichment
BAD_ALBUM_PATTERNS = [
    # French/other artists that Bladee tracks got matched to
    "Jok'Chirac",
    "La Ballade des Dalton",
    "Lucky Luke",
    "Blade (Remixes)",  # Wrong "Blade" 
    "El Ultimo Adiós",
    "Everything I Have, Vol.",
    "Innocence v2",
    # Generic bad patterns
    "Remixes",
    "Remix EP",
]


async def find_single_like_albums():
    """Find tracks where album name equals track title (likely wrong)"""
    async with get_session() as session:
        result = await session.execute(
            select(Track).where(
                Track.album.isnot(None),
                Track.album != "",
                Track.enrichment_status == "completed"
            )
        )
        tracks = result.scalars().all()
        
        single_like = []
        for track in tracks:
            if track.album and track.title:
                # Normalize for comparison
                album_norm = track.album.lower().strip()
                title_norm = track.title.lower().strip()
                
                if album_norm == title_norm:
                    single_like.append(track)
        
        return single_like


async def find_bad_pattern_albums():
    """Find tracks with known bad album patterns"""
    async with get_session() as session:
        tracks = []
        for pattern in BAD_ALBUM_PATTERNS:
            result = await session.execute(
                select(Track).where(
                    Track.album.ilike(f"%{pattern}%"),
                    Track.enrichment_status == "completed"
                )
            )
            tracks.extend(result.scalars().all())
        
        return tracks


async def reset_track_enrichment(track_ids: list[int]):
    """Reset enrichment for given track IDs"""
    if not track_ids:
        return 0
        
    async with get_session() as session:
        result = await session.execute(
            update(Track)
            .where(Track.id.in_(track_ids))
            .values(
                album=None,
                deezer_album_id=None,
                cover_url=None,
                genre=None,
                enrichment_status="pending"
            )
        )
        await session.commit()
        return result.rowcount


async def delete_auto_album_playlists(album_names: list[str]):
    """Delete auto-album playlists with given names"""
    if not album_names:
        return 0
        
    deleted = 0
    async with get_session() as session:
        for name in album_names:
            result = await session.execute(
                select(Playlist).where(
                    Playlist.is_auto_album == True,
                    func.lower(Playlist.name) == name.lower()
                )
            )
            playlists = result.scalars().all()
            
            for playlist in playlists:
                # Delete playlist tracks first
                await session.execute(
                    PlaylistTrack.__table__.delete().where(
                        PlaylistTrack.playlist_id == playlist.id
                    )
                )
                await session.delete(playlist)
                deleted += 1
        
        await session.commit()
    
    return deleted


async def main():
    print("=" * 60)
    print("FIX WRONG ENRICHMENT DATA")
    print("=" * 60)
    
    # Find problematic tracks
    print("\n1. Finding tracks with album = title (single-like)...")
    single_like = await find_single_like_albums()
    print(f"   Found {len(single_like)} tracks")
    
    if single_like:
        print("\n   Examples:")
        for track in single_like[:10]:
            print(f"   - [{track.id}] {track.artist} - {track.title} -> album: {track.album}")
    
    print("\n2. Finding tracks with known bad album patterns...")
    bad_pattern = await find_bad_pattern_albums()
    print(f"   Found {len(bad_pattern)} tracks")
    
    if bad_pattern:
        print("\n   Examples:")
        for track in bad_pattern[:10]:
            print(f"   - [{track.id}] {track.artist} - {track.title} -> album: {track.album}")
    
    # Combine and deduplicate
    all_bad_tracks = {t.id: t for t in single_like + bad_pattern}
    total_bad = len(all_bad_tracks)
    
    print(f"\n3. Total tracks to fix: {total_bad}")
    
    if total_bad == 0:
        print("\n✓ No problematic tracks found!")
        return
    
    # Collect album names to delete
    bad_album_names = set()
    for track in all_bad_tracks.values():
        if track.album:
            bad_album_names.add(track.album)
    
    # Confirm action
    print(f"\nThis will:")
    print(f"  - Reset enrichment for {total_bad} tracks")
    print(f"  - Delete up to {len(bad_album_names)} auto-album playlists")
    
    confirm = input("\nProceed? [y/N]: ").strip().lower()
    if confirm != 'y':
        print("Aborted.")
        return
    
    # Execute fixes
    print("\n4. Resetting track enrichment...")
    reset_count = await reset_track_enrichment(list(all_bad_tracks.keys()))
    print(f"   Reset {reset_count} tracks")
    
    print("\n5. Deleting bad auto-album playlists...")
    deleted_count = await delete_auto_album_playlists(list(bad_album_names))
    print(f"   Deleted {deleted_count} playlists")
    
    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)
    print(f"\nTracks will be re-enriched automatically by the bot.")
    print(f"Albums will be re-assembled after enrichment completes.")


if __name__ == "__main__":
    asyncio.run(main())

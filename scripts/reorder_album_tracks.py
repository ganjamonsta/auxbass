"""
Script to reorder tracks in album playlists according to Deezer track order.
This fixes albums where tracks are in wrong order.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.database import get_session
from shared.models import Track, Playlist, PlaylistTrack, UserLibrary
from sqlalchemy import select, func
from bot.services.albums import album_service
from bot.services.metadata import metadata_service


async def reorder_album(playlist: Playlist) -> tuple[bool, str]:
    """Reorder tracks in a playlist according to Deezer order"""
    
    # Get all tracks for this album from user's library
    async with get_session() as session:
        result = await session.execute(
            select(Track)
            .join(UserLibrary, UserLibrary.track_id == Track.id)
            .where(
                UserLibrary.user_id == playlist.user_id,
                func.lower(Track.album) == playlist.name.lower().strip()
            )
        )
        tracks = list(result.scalars().all())
    
    if not tracks:
        return False, "no tracks"
    
    # Try to get deezer_album_id from tracks if playlist doesn't have it
    deezer_album_id = playlist.deezer_album_id
    if not deezer_album_id:
        for track in tracks:
            if track.deezer_album_id:
                deezer_album_id = track.deezer_album_id
                break
    
    if not deezer_album_id:
        return False, "no deezer_album_id"
    
    # Use album service to update with reorder
    try:
        updated = await album_service.update_album_playlist(
            playlist=playlist,
            tracks=tracks,
            deezer_album_id=deezer_album_id,
            reorder=True
        )
        return updated, "reordered" if updated else "no changes"
    except Exception as e:
        return False, str(e)


async def main():
    print("🔄 Reordering album tracks according to Deezer order...\n")
    
    async with get_session() as session:
        # Get all auto-album playlists that have deezer_album_id or tracks with it
        result = await session.execute(
            select(Playlist)
            .where(Playlist.is_auto_album == True)
            .order_by(Playlist.name)
        )
        playlists = list(result.scalars().all())
    
    print(f"📊 Found {len(playlists)} album playlists\n")
    
    reordered = 0
    skipped = 0
    failed = 0
    
    for i, playlist in enumerate(playlists, 1):
        artist = playlist.album_artist or "Unknown"
        print(f"[{i}/{len(playlists)}] {artist} — {playlist.name}", end="")
        
        try:
            success, reason = await reorder_album(playlist)
            if success:
                print(f" ✅ {reason}")
                reordered += 1
            else:
                print(f" ⏭️ {reason}")
                skipped += 1
        except Exception as e:
            print(f" ❌ error: {e}")
            failed += 1
    
    # Close session
    await metadata_service.close()
    
    print(f"\n✨ Done!")
    print(f"   Reordered: {reordered}")
    print(f"   Skipped: {skipped}")
    print(f"   Failed: {failed}")


if __name__ == "__main__":
    asyncio.run(main())

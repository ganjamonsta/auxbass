"""
Script to rebuild all album playlists.
Cleans up empty albums and reassembles them from tracks.

Run from /opt/tg_player: python scripts/archive/rebuild_albums.py
"""
import asyncio
import sys
from pathlib import Path

# Go up two levels: archive -> scripts -> project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import get_session
from shared.models import Track, Playlist, PlaylistTrack, UserLibrary
from sqlalchemy import select, distinct, func


async def rebuild_all_albums():
    """Rebuild album playlists for all users"""
    from bot.services.albums import album_service
    from bot.services.metadata import metadata_service
    
    print("🔍 Finding users with tracks...")
    
    async with get_session() as session:
        # Get all user IDs from UserLibrary (not Track.user_id!)
        result = await session.execute(
            select(distinct(UserLibrary.user_id))
        )
        user_ids = [row[0] for row in result.all()]
    
    print(f"📊 Found {len(user_ids)} users with album tracks")
    
    for user_id in user_ids:
        print(f"\n👤 Processing user {user_id}...")
        
        try:
            stats = await album_service.assemble_albums_for_user(user_id)
            print(f"   ✅ Created: {stats['created']}, Updated: {stats['updated']}, Skipped: {stats['skipped']}")
            
            if stats.get('cleaned'):
                print(f"   🧹 Cleaned: {stats['cleaned']} empty albums")
                
            for album in stats.get('albums', [])[:15]:  # Limit output
                track_count = album.get('track_count', '?')
                print(f"      • {album['name']} ({album.get('action', 'processed')}, {track_count} tracks)")
            
            if len(stats.get('albums', [])) > 15:
                print(f"      ... and {len(stats['albums']) - 15} more")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Close any open sessions
    await metadata_service.close()
    
    print("\n✨ Done!")


async def show_album_stats():
    """Show statistics about albums"""
    async with get_session() as session:
        # Count all auto-album playlists
        total = await session.scalar(
            select(func.count(Playlist.id))
            .where(Playlist.is_auto_album == True)
        )
        
        # Find empty ones
        result = await session.execute(
            select(Playlist)
            .where(Playlist.is_auto_album == True)
        )
        playlists = result.scalars().all()
        
        empty_count = 0
        print("\n📊 Album Statistics:")
        print(f"   Total auto-albums: {total}")
        
        for pl in playlists:
            track_count = await session.scalar(
                select(func.count(PlaylistTrack.id))
                .where(PlaylistTrack.playlist_id == pl.id)
            )
            if track_count == 0:
                empty_count += 1
                print(f"   ⚠️  Empty album: {pl.name} (id={pl.id}, user={pl.user_id})")
        
        print(f"   Empty albums: {empty_count}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--stats":
        asyncio.run(show_album_stats())
    else:
        asyncio.run(rebuild_all_albums())

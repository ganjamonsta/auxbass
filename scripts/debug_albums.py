"""
Debug script to understand why albums are created with 0 tracks
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.database import get_session
from shared.models import Track, Playlist, PlaylistTrack, UserLibrary
from sqlalchemy import select, func


async def debug_user_albums(user_id: int = 874295897):
    """Debug album creation for a specific user"""
    
    print(f"🔍 Debugging albums for user {user_id}\n")
    
    async with get_session() as session:
        # 1. Check UserLibrary entries
        lib_result = await session.execute(
            select(func.count(UserLibrary.id))
            .where(UserLibrary.user_id == user_id)
        )
        lib_count = lib_result.scalar()
        print(f"📚 UserLibrary entries: {lib_count}")
        
        # 2. Check tracks with albums in user's library
        tracks_result = await session.execute(
            select(Track)
            .join(UserLibrary, UserLibrary.track_id == Track.id)
            .where(
                UserLibrary.user_id == user_id,
                Track.album.isnot(None),
                Track.album != ""
            )
            .limit(20)
        )
        tracks = list(tracks_result.scalars().all())
        print(f"🎵 Tracks with albums in library: {len(tracks)}")
        
        if tracks:
            print("\n📋 Sample tracks:")
            for t in tracks[:10]:
                print(f"   • {t.artist} - {t.title}")
                print(f"     Album: '{t.album}' | deezer_album_id: {t.deezer_album_id}")
        
        # 3. Check a specific Russian album
        print("\n\n🔍 Checking Russian albums...")
        
        # Find tracks with Cyrillic in album name
        all_tracks_result = await session.execute(
            select(Track)
            .join(UserLibrary, UserLibrary.track_id == Track.id)
            .where(UserLibrary.user_id == user_id)
        )
        all_tracks = list(all_tracks_result.scalars().all())
        
        russian_albums = {}
        for t in all_tracks:
            if t.album and any(ord(c) > 127 for c in t.album):
                key = t.album.lower().strip()
                if key not in russian_albums:
                    russian_albums[key] = []
                russian_albums[key].append(t)
        
        print(f"📝 Russian albums found: {len(russian_albums)}")
        for album_name, tracks in list(russian_albums.items())[:5]:
            print(f"\n   Album: '{album_name}'")
            print(f"   Tracks: {len(tracks)}")
            for t in tracks:
                print(f"      • {t.title} (id={t.id})")
        
        # 4. Check empty playlists
        print("\n\n🔍 Checking empty album playlists...")
        empty_playlists_result = await session.execute(
            select(Playlist)
            .where(
                Playlist.user_id == user_id,
                Playlist.is_auto_album == True
            )
        )
        playlists = list(empty_playlists_result.scalars().all())
        
        empty_count = 0
        for pl in playlists:
            track_count = await session.scalar(
                select(func.count(PlaylistTrack.id))
                .where(PlaylistTrack.playlist_id == pl.id)
            )
            if track_count == 0:
                empty_count += 1
                # Try to find matching tracks
                matching = await session.execute(
                    select(func.count(Track.id))
                    .join(UserLibrary, UserLibrary.track_id == Track.id)
                    .where(
                        UserLibrary.user_id == user_id,
                        func.lower(Track.album) == pl.name.lower().strip()
                    )
                )
                match_count = matching.scalar()
                print(f"   ❌ Empty: '{pl.name}' - potential matches: {match_count}")
        
        print(f"\n📊 Total empty playlists: {empty_count}")


if __name__ == "__main__":
    asyncio.run(debug_user_albums())

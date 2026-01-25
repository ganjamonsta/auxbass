"""
Migration script to merge duplicate auto-album playlists and deduplicate tracks.
Finds albums with same name (case-insensitive) and merges them into one.
Also removes duplicate tracks (same title) within each album.
"""
import asyncio
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.database import get_session, init_db
from shared.models import Playlist, PlaylistTrack, Track
from sqlalchemy import select, func, delete


async def deduplicate_album_tracks():
    """Remove duplicate tracks (by title) from all auto-album playlists"""
    async with get_session() as session:
        # Get all auto-album playlists
        result = await session.execute(
            select(Playlist).where(Playlist.is_auto_album == True)
        )
        all_albums = list(result.scalars().all())
        
        total_removed = 0
        
        for album in all_albums:
            # Get all tracks in this playlist with their info
            result = await session.execute(
                select(PlaylistTrack, Track)
                .join(Track, PlaylistTrack.track_id == Track.id)
                .where(PlaylistTrack.playlist_id == album.id)
                .order_by(PlaylistTrack.position)
            )
            playlist_tracks = list(result.all())
            
            # Find duplicates by title (case-insensitive)
            seen_titles = {}
            duplicates_to_remove = []
            
            for pt, track in playlist_tracks:
                title_key = track.title.lower().strip() if track.title else str(track.id)
                
                if title_key in seen_titles:
                    # This is a duplicate
                    existing_pt, existing_track = seen_titles[title_key]
                    
                    # Decide which to keep - prefer one with cover_url
                    if not existing_track.cover_url and track.cover_url:
                        # Remove the existing one, keep this one
                        duplicates_to_remove.append(existing_pt.id)
                        seen_titles[title_key] = (pt, track)
                    else:
                        # Remove this one
                        duplicates_to_remove.append(pt.id)
                else:
                    seen_titles[title_key] = (pt, track)
            
            if duplicates_to_remove:
                print(f"Album '{album.name}': removing {len(duplicates_to_remove)} duplicate track(s)")
                
                # Remove duplicates
                await session.execute(
                    delete(PlaylistTrack)
                    .where(PlaylistTrack.id.in_(duplicates_to_remove))
                )
                
                total_removed += len(duplicates_to_remove)
                
                # Update track count in description
                new_count = len(playlist_tracks) - len(duplicates_to_remove)
                album.description = f"Автоальбом • {new_count} треков"
        
        await session.commit()
        return total_removed


async def merge_duplicate_albums():
    """Find and merge duplicate auto-album playlists"""
    await init_db()
    
    async with get_session() as session:
        # Get all auto-album playlists
        result = await session.execute(
            select(Playlist).where(Playlist.is_auto_album == True)
        )
        all_albums = list(result.scalars().all())
        
        # Group by user_id and album name (case-insensitive)
        user_albums = defaultdict(lambda: defaultdict(list))
        for album in all_albums:
            name_key = album.name.lower().strip() if album.name else ""
            if name_key:
                user_albums[album.user_id][name_key].append(album)
        
        merged_count = 0
        deleted_count = 0
        
        for user_id, albums_by_name in user_albums.items():
            for name_key, playlists in albums_by_name.items():
                if len(playlists) <= 1:
                    continue
                
                # Sort by track count descending - keep the one with most tracks
                playlists_with_counts = []
                for pl in playlists:
                    count_result = await session.execute(
                        select(func.count(PlaylistTrack.id))
                        .where(PlaylistTrack.playlist_id == pl.id)
                    )
                    count = count_result.scalar() or 0
                    playlists_with_counts.append((pl, count))
                
                playlists_with_counts.sort(key=lambda x: x[1], reverse=True)
                
                # Keep first (most tracks), merge others into it
                main_playlist, main_count = playlists_with_counts[0]
                print(f"\nMerging duplicates for '{main_playlist.name}' (user {user_id}):")
                print(f"  Main playlist: id={main_playlist.id}, tracks={main_count}")
                
                # Get existing track IDs in main playlist
                result = await session.execute(
                    select(PlaylistTrack.track_id)
                    .where(PlaylistTrack.playlist_id == main_playlist.id)
                )
                existing_track_ids = {row[0] for row in result.all()}
                
                # Get max position in main playlist
                result = await session.execute(
                    select(func.max(PlaylistTrack.position))
                    .where(PlaylistTrack.playlist_id == main_playlist.id)
                )
                max_pos = result.scalar() or 0
                
                # Collect all unique artists from all playlists
                all_artists = set()
                if main_playlist.album_artist:
                    for artist in main_playlist.album_artist.split(" & "):
                        all_artists.add(artist.replace(" и др.", "").strip())
                
                # Process duplicate playlists
                for dup_playlist, dup_count in playlists_with_counts[1:]:
                    print(f"  Merging: id={dup_playlist.id}, tracks={dup_count}")
                    
                    # Collect artists
                    if dup_playlist.album_artist:
                        for artist in dup_playlist.album_artist.split(" & "):
                            all_artists.add(artist.replace(" и др.", "").strip())
                    
                    # Get tracks from duplicate playlist
                    result = await session.execute(
                        select(PlaylistTrack)
                        .where(PlaylistTrack.playlist_id == dup_playlist.id)
                        .order_by(PlaylistTrack.position)
                    )
                    dup_tracks = list(result.scalars().all())
                    
                    # Move unique tracks to main playlist
                    added = 0
                    for pt in dup_tracks:
                        if pt.track_id not in existing_track_ids:
                            max_pos += 1
                            new_pt = PlaylistTrack(
                                playlist_id=main_playlist.id,
                                track_id=pt.track_id,
                                position=max_pos
                            )
                            session.add(new_pt)
                            existing_track_ids.add(pt.track_id)
                            added += 1
                    
                    print(f"    Added {added} unique tracks to main playlist")
                    
                    # Delete duplicate playlist tracks
                    await session.execute(
                        delete(PlaylistTrack)
                        .where(PlaylistTrack.playlist_id == dup_playlist.id)
                    )
                    
                    # Delete duplicate playlist
                    await session.delete(dup_playlist)
                    deleted_count += 1
                
                # Update main playlist with all artists
                if all_artists:
                    artists_list = sorted(all_artists)
                    if len(artists_list) > 2:
                        main_playlist.album_artist = f"{artists_list[0]} и др."
                    elif len(artists_list) == 2:
                        main_playlist.album_artist = " & ".join(artists_list)
                    else:
                        main_playlist.album_artist = artists_list[0]
                
                # Update description with new track count
                main_playlist.description = f"Автоальбом • {len(existing_track_ids)} треков"
                
                # Update cover if missing
                if not main_playlist.cover_url:
                    for dup_playlist, _ in playlists_with_counts[1:]:
                        if dup_playlist.cover_url:
                            main_playlist.cover_url = dup_playlist.cover_url
                            break
                
                merged_count += 1
        
        await session.commit()
        
        print(f"\n=== Merge Summary ===")
        print(f"Album groups merged: {merged_count}")
        print(f"Duplicate playlists deleted: {deleted_count}")
    
    # Now deduplicate tracks within each album
    print("\n=== Deduplicating tracks within albums ===")
    removed = await deduplicate_album_tracks()
    print(f"\nTotal duplicate tracks removed: {removed}")


if __name__ == "__main__":
    asyncio.run(merge_duplicate_albums())

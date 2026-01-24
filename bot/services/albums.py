"""
TG Player - Auto Album Assembly Service
Automatically creates playlists from tracks with matching album/artist
"""
import logging
from typing import Optional, List, Dict
from sqlalchemy import select, func, delete

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import get_session
from shared.models import Track, Playlist, PlaylistTrack, UserLibrary
from .metadata import metadata_service

logger = logging.getLogger(__name__)


class AlbumAssemblyService:
    """Service for automatically assembling albums from user's tracks"""
    
    # Minimum tracks to consider as album (1 = allow singles)
    MIN_TRACKS_FOR_ALBUM = 1
    
    async def get_album_candidates(self, user_id: int) -> List[Dict]:
        """
        Find potential albums from user's tracks.
        Groups by album name (case-insensitive) as primary key.
        This ensures tracks from different sources with same album name 
        but different metadata (artist, deezer_album_id) are grouped together.
        Aggregates all artists for the album.
        Returns list of album candidates with track counts.
        """
        async with get_session() as session:
            # Get all tracks in user's library with album info
            result = await session.execute(
                select(Track)
                .join(UserLibrary, UserLibrary.track_id == Track.id)
                .where(
                    UserLibrary.user_id == user_id,
                    Track.album.isnot(None),
                    Track.album != "",
                )
            )
            tracks = list(result.scalars().all())
            
            # Group by album name (normalized) - this ensures all tracks
            # with same album name are grouped together regardless of artist/source
            albums: Dict[str, Dict] = {}
            
            for track in tracks:
                # Use album name as primary key (case-insensitive, trimmed)
                key = track.album.lower().strip()
                
                if key not in albums:
                    albums[key] = {
                        "album": track.album,
                        "deezer_album_ids": set(),  # Collect all deezer IDs
                        "cover_url": track.cover_url,
                        "artists": set(),
                        "track_ids": set(),
                        "total_duration": 0,
                    }
                
                album_data = albums[key]
                
                # Collect all artists
                if track.artist:
                    album_data["artists"].add(track.artist)
                
                # Track unique tracks
                album_data["track_ids"].add(track.id)
                album_data["total_duration"] += track.duration or 0
                
                # Update cover_url if we don't have one
                if not album_data["cover_url"] and track.cover_url:
                    album_data["cover_url"] = track.cover_url
                
                # Collect all deezer_album_ids
                if track.deezer_album_id:
                    album_data["deezer_album_ids"].add(track.deezer_album_id)
            
            # Convert to list and filter by minimum tracks
            candidates = []
            for key, data in albums.items():
                if len(data["track_ids"]) < self.MIN_TRACKS_FOR_ALBUM:
                    continue
                
                # Determine main artist (most common or first)
                artists_list = sorted(data["artists"])
                main_artist = artists_list[0] if artists_list else "Unknown"
                
                # Pick the first deezer_album_id if any exist
                deezer_ids = list(data["deezer_album_ids"])
                deezer_album_id = deezer_ids[0] if deezer_ids else None
                
                candidates.append({
                    "artist": main_artist,
                    "all_artists": artists_list,
                    "album": data["album"],
                    "deezer_album_id": deezer_album_id,
                    "cover_url": data["cover_url"],
                    "track_count": len(data["track_ids"]),
                    "total_duration": data["total_duration"],
                })
            
            # Sort by track count descending
            candidates.sort(key=lambda x: x["track_count"], reverse=True)
            
            return candidates
    
    async def _cleanup_empty_albums(self, user_id: int) -> int:
        """
        Remove auto-album playlists that have no tracks.
        Returns count of deleted albums.
        """
        async with get_session() as session:
            # Find all auto-album playlists for user
            result = await session.execute(
                select(Playlist).where(
                    Playlist.user_id == user_id,
                    Playlist.is_auto_album == True,
                )
            )
            albums = result.scalars().all()
            
            deleted_count = 0
            for album in albums:
                # Check if album has any tracks
                track_count = await session.scalar(
                    select(func.count(PlaylistTrack.id))
                    .where(PlaylistTrack.playlist_id == album.id)
                )
                
                if track_count == 0:
                    logger.info(f"Removing empty album playlist: {album.name} (id={album.id})")
                    await session.delete(album)
                    deleted_count += 1
            
            if deleted_count > 0:
                await session.commit()
                logger.info(f"Cleaned up {deleted_count} empty album playlists for user {user_id}")
            
            return deleted_count
    
    async def check_existing_album_playlist(
        self, 
        user_id: int, 
        album: str,
        deezer_album_id: Optional[int] = None
    ) -> Optional[Playlist]:
        """
        Check if auto-album playlist already exists for this album.
        Searches by album name (case-insensitive) as primary match.
        """
        async with get_session() as session:
            # Get all album playlists for user
            result = await session.execute(
                select(Playlist).where(
                    Playlist.user_id == user_id,
                    Playlist.is_auto_album == True,
                )
            )
            playlists = result.scalars().all()
            
            album_lower = album.lower().strip()
            for pl in playlists:
                if not pl.name:
                    continue
                    
                name_lower = pl.name.lower().strip()
                
                # Match by exact album name (new format)
                if name_lower == album_lower:
                    return pl
                
                # Match by old format "Artist — Album"
                if name_lower.endswith(f" — {album_lower}"):
                    return pl
                
                # Match if name contains album after separator
                if " — " in pl.name:
                    parts = pl.name.split(" — ", 1)
                    if len(parts) > 1 and parts[1].lower().strip() == album_lower:
                        return pl
            
            return None
    
    async def get_album_tracks(
        self, 
        user_id: int, 
        album: str,
        deezer_album_id: Optional[int] = None
    ) -> List[Track]:
        """
        Get all user's tracks for a specific album.
        Groups by album name (case-insensitive) to ensure all tracks 
        with same album name are included regardless of artist/source.
        Deduplicates by title to avoid duplicate tracks from different sources.
        """
        async with get_session() as session:
            # Get tracks from user's library by album name
            result = await session.execute(
                select(Track)
                .join(UserLibrary, UserLibrary.track_id == Track.id)
                .where(
                    UserLibrary.user_id == user_id,
                    func.lower(Track.album) == album.lower().strip()
                )
                .order_by(Track.title)
            )
            
            all_tracks = list(result.scalars().all())
            
            # Deduplicate by title (case-insensitive)
            # Keep the track with cover_url or higher quality metadata
            seen_titles = {}
            unique_tracks = []
            for track in all_tracks:
                title_key = track.title.lower().strip() if track.title else str(track.id)
                if title_key not in seen_titles:
                    seen_titles[title_key] = track
                    unique_tracks.append(track)
                else:
                    # Prefer track with cover_url
                    existing = seen_titles[title_key]
                    if not existing.cover_url and track.cover_url:
                        # Replace with better metadata
                        idx = unique_tracks.index(existing)
                        unique_tracks[idx] = track
                        seen_titles[title_key] = track
            
            return unique_tracks
    
    async def get_deezer_album_tracklist(self, album_id: int) -> Optional[List[Dict]]:
        """
        Get full tracklist from Deezer to determine correct order.
        Returns list of {title, position, duration}
        """
        try:
            session = await metadata_service._get_session()
            await metadata_service._rate_limit()
            
            async with session.get(
                f"{metadata_service.DEEZER_API}/album/{album_id}/tracks"
            ) as resp:
                if resp.status != 200:
                    return None
                
                data = await resp.json()
                tracks = data.get("data", [])
                
                return [
                    {
                        "title": t.get("title"),
                        "position": t.get("track_position", i + 1),
                        "duration": t.get("duration"),
                        "deezer_id": t.get("id"),
                    }
                    for i, t in enumerate(tracks)
                ]
        except Exception as e:
            logger.error(f"Failed to get Deezer tracklist: {e}")
            return None
    
    async def create_album_playlist(
        self,
        user_id: int,
        artist: str,
        album: str,
        tracks: List[Track],
        deezer_album_id: Optional[int] = None,
        cover_url: Optional[str] = None
    ) -> Playlist:
        """Create a new auto-album playlist from tracks"""
        async with get_session() as session:
            # Store album name only, artist is separate
            playlist = Playlist(
                user_id=user_id,
                name=album,  # Just album name
                album_artist=artist,  # Artist stored separately
                description=f"Автоальбом • {len(tracks)} треков",
                is_auto_album=True,
                deezer_album_id=deezer_album_id,
                cover_url=cover_url,
            )
            session.add(playlist)
            await session.flush()
            
            # Try to get correct track order from Deezer
            track_order = {}
            if deezer_album_id:
                deezer_tracks = await self.get_deezer_album_tracklist(deezer_album_id)
                if deezer_tracks:
                    # Create mapping: lowercase title -> position
                    for dt in deezer_tracks:
                        if dt.get("title"):
                            track_order[dt["title"].lower()] = dt["position"]
            
            # Sort tracks by Deezer order or alphabetically
            def get_position(track):
                if track.title:
                    pos = track_order.get(track.title.lower())
                    if pos:
                        return (0, pos)  # Has Deezer position
                return (1, track.title or "")  # Fallback to alphabetical
            
            sorted_tracks = sorted(tracks, key=get_position)
            
            # Add tracks to playlist
            for position, track in enumerate(sorted_tracks, start=1):
                pt = PlaylistTrack(
                    playlist_id=playlist.id,
                    track_id=track.id,
                    position=position
                )
                session.add(pt)
            
            await session.commit()
            
            logger.info(f"Created auto-album: {artist} — {album} ({len(tracks)} tracks)")
            return playlist
    
    async def update_album_playlist(
        self,
        playlist: Playlist,
        tracks: List[Track],
        deezer_album_id: Optional[int] = None,
        cover_url: Optional[str] = None,
        reorder: bool = False
    ) -> bool:
        """Update existing album playlist with new tracks and cover.
        If reorder=True, reorders all tracks according to Deezer tracklist.
        """
        async with get_session() as session:
            # Attach playlist to this session
            playlist = await session.merge(playlist)
            
            # Update deezer_album_id if not set
            if deezer_album_id and not playlist.deezer_album_id:
                playlist.deezer_album_id = deezer_album_id
            
            # Update cover if not set and we have one
            cover_updated = False
            if cover_url and not playlist.cover_url:
                playlist.cover_url = cover_url
                cover_updated = True
            
            # Get existing track IDs in playlist
            result = await session.execute(
                select(PlaylistTrack.track_id)
                .where(PlaylistTrack.playlist_id == playlist.id)
            )
            existing_track_ids = {row[0] for row in result.all()}
            
            # Find new tracks
            new_tracks = [t for t in tracks if t.id not in existing_track_ids]
            
            if not new_tracks and not cover_updated and not reorder:
                return False
            
            # If reordering or adding new tracks, rebuild the playlist order
            if reorder or new_tracks:
                # Get Deezer track order
                track_order = {}
                album_id = deezer_album_id or playlist.deezer_album_id
                if album_id:
                    deezer_tracks = await self.get_deezer_album_tracklist(album_id)
                    if deezer_tracks:
                        for dt in deezer_tracks:
                            if dt.get("title"):
                                track_order[dt["title"].lower().strip()] = dt["position"]
                
                if reorder and track_order:
                    # Delete all existing playlist tracks
                    await session.execute(
                        delete(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist.id)
                    )
                    
                    # Sort all tracks by Deezer order
                    def get_position(track):
                        if track.title:
                            pos = track_order.get(track.title.lower().strip())
                            if pos:
                                return (0, pos)
                        return (1, track.title or "")
                    
                    sorted_tracks = sorted(tracks, key=get_position)
                    
                    # Add all tracks with correct positions
                    for position, track in enumerate(sorted_tracks, start=1):
                        pt = PlaylistTrack(
                            playlist_id=playlist.id,
                            track_id=track.id,
                            position=position
                        )
                        session.add(pt)
                else:
                    # Just add new tracks at end
                    result = await session.execute(
                        select(func.max(PlaylistTrack.position))
                        .where(PlaylistTrack.playlist_id == playlist.id)
                    )
                    max_pos = result.scalar() or 0
                    
                    for i, track in enumerate(new_tracks, start=1):
                        pt = PlaylistTrack(
                            playlist_id=playlist.id,
                            track_id=track.id,
                            position=max_pos + i
                        )
                        session.add(pt)
            
            # Update description
            total_tracks = len(tracks) if reorder else len(existing_track_ids) + len(new_tracks)
            playlist.description = f"Автоальбом • {total_tracks} треков"
            
            await session.commit()
            
            action = "reordered" if reorder else f"+{len(new_tracks)} tracks"
            logger.info(f"Updated auto-album {playlist.name}: {action}")
            return True
    
    async def assemble_albums_for_user(self, user_id: int) -> Dict:
        """
        Main method: find and create/update all album playlists for user.
        Returns stats about created/updated albums.
        """
        stats = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "cleaned": 0,
            "albums": []
        }
        
        # First, clean up empty album playlists
        await self._cleanup_empty_albums(user_id)
        
        candidates = await self.get_album_candidates(user_id)
        
        for candidate in candidates:
            album = candidate["album"]
            deezer_album_id = candidate.get("deezer_album_id")
            cover_url = candidate.get("cover_url")
            all_artists = candidate.get("all_artists", [candidate.get("artist", "Unknown")])
            
            # Format artist display name
            if len(all_artists) > 2:
                artist_display = f"{all_artists[0]} и др."
            elif len(all_artists) == 2:
                artist_display = " & ".join(all_artists)
            else:
                artist_display = all_artists[0] if all_artists else "Unknown"
            
            # Check if playlist already exists
            existing = await self.check_existing_album_playlist(
                user_id, album, deezer_album_id
            )
            
            # Get all tracks for this album
            tracks = await self.get_album_tracks(
                user_id, album, deezer_album_id
            )
            
            if existing:
                # Update existing playlist
                updated = await self.update_album_playlist(
                    existing, tracks, deezer_album_id, cover_url
                )
                if updated:
                    stats["updated"] += 1
                    stats["albums"].append({
                        "name": f"{artist_display} — {album}",
                        "action": "updated"
                    })
                else:
                    stats["skipped"] += 1
            else:
                # Create new playlist
                await self.create_album_playlist(
                    user_id=user_id,
                    artist=artist_display,
                    album=album,
                    tracks=tracks,
                    deezer_album_id=deezer_album_id,
                    cover_url=cover_url
                )
                stats["created"] += 1
                stats["albums"].append({
                    "name": f"{artist_display} — {album}",
                    "action": "created",
                    "track_count": len(tracks)
                })
        
        return stats


# Global instance
album_service = AlbumAssemblyService()

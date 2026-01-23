"""
TG Player - Auto Album Assembly Service
Automatically creates playlists from tracks with matching album/artist
"""
import logging
from typing import Optional, List, Dict
from sqlalchemy import select, func, and_, or_

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import get_session
from shared.models import Track, Playlist, PlaylistTrack
from .metadata import metadata_service

logger = logging.getLogger(__name__)


class AlbumAssemblyService:
    """Service for automatically assembling albums from user's tracks"""
    
    # Minimum tracks to consider as album
    MIN_TRACKS_FOR_ALBUM = 2
    
    async def get_album_candidates(self, user_id: int) -> List[Dict]:
        """
        Find potential albums from user's tracks.
        Groups by (artist, album) or (artist, deezer_album_id)
        Returns list of album candidates with track counts.
        """
        async with get_session() as session:
            # Find tracks grouped by artist + album (or deezer_album_id)
            result = await session.execute(
                select(
                    Track.artist,
                    Track.album,
                    Track.deezer_album_id,
                    Track.cover_url,
                    func.count(Track.id).label("track_count"),
                    func.sum(Track.duration).label("total_duration")
                )
                .where(
                    Track.user_id == user_id,
                    Track.album.isnot(None),
                    Track.album != "",
                    Track.artist.isnot(None),
                    Track.artist != ""
                )
                .group_by(
                    Track.artist,
                    Track.album,
                    Track.deezer_album_id,
                    Track.cover_url
                )
                .having(func.count(Track.id) >= self.MIN_TRACKS_FOR_ALBUM)
                .order_by(func.count(Track.id).desc())
            )
            
            candidates = []
            for row in result.all():
                candidates.append({
                    "artist": row.artist,
                    "album": row.album,
                    "deezer_album_id": row.deezer_album_id,
                    "cover_url": row.cover_url,
                    "track_count": row.track_count,
                    "total_duration": row.total_duration or 0,
                })
            
            return candidates
    
    async def check_existing_album_playlist(
        self, 
        user_id: int, 
        artist: str, 
        album: str,
        deezer_album_id: Optional[int] = None
    ) -> Optional[Playlist]:
        """Check if auto-album playlist already exists for this album"""
        async with get_session() as session:
            # First try to match by deezer_album_id if available
            if deezer_album_id:
                result = await session.execute(
                    select(Playlist).where(
                        Playlist.user_id == user_id,
                        Playlist.is_auto_album == True,
                        Playlist.deezer_album_id == deezer_album_id
                    )
                )
                playlist = result.scalar()
                if playlist:
                    return playlist
            
            # Fallback to name matching
            album_name = f"{artist} — {album}"
            result = await session.execute(
                select(Playlist).where(
                    Playlist.user_id == user_id,
                    Playlist.is_auto_album == True,
                    Playlist.name == album_name
                )
            )
            return result.scalar()
    
    async def get_album_tracks(
        self, 
        user_id: int, 
        artist: str, 
        album: str,
        deezer_album_id: Optional[int] = None
    ) -> List[Track]:
        """Get all user's tracks for a specific album"""
        async with get_session() as session:
            conditions = [
                Track.user_id == user_id,
                Track.artist == artist,
            ]
            
            # Prefer deezer_album_id match if available
            if deezer_album_id:
                conditions.append(
                    or_(
                        Track.deezer_album_id == deezer_album_id,
                        Track.album == album
                    )
                )
            else:
                conditions.append(Track.album == album)
            
            result = await session.execute(
                select(Track)
                .where(and_(*conditions))
                .order_by(Track.title)  # TODO: order by track number if available
            )
            
            return list(result.scalars().all())
    
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
            album_name = f"{artist} — {album}"
            
            playlist = Playlist(
                user_id=user_id,
                name=album_name,
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
            
            logger.info(f"Created auto-album: {album_name} ({len(tracks)} tracks)")
            return playlist
    
    async def update_album_playlist(
        self,
        playlist: Playlist,
        tracks: List[Track],
        deezer_album_id: Optional[int] = None
    ) -> bool:
        """Update existing album playlist with new tracks"""
        async with get_session() as session:
            # Get existing track IDs in playlist
            result = await session.execute(
                select(PlaylistTrack.track_id)
                .where(PlaylistTrack.playlist_id == playlist.id)
            )
            existing_track_ids = {row[0] for row in result.all()}
            
            # Find new tracks
            new_tracks = [t for t in tracks if t.id not in existing_track_ids]
            
            if not new_tracks:
                return False
            
            # Get max position
            result = await session.execute(
                select(func.max(PlaylistTrack.position))
                .where(PlaylistTrack.playlist_id == playlist.id)
            )
            max_pos = result.scalar() or 0
            
            # Add new tracks
            for i, track in enumerate(new_tracks, start=1):
                pt = PlaylistTrack(
                    playlist_id=playlist.id,
                    track_id=track.id,
                    position=max_pos + i
                )
                session.add(pt)
            
            # Update description
            playlist.description = f"Автоальбом • {len(existing_track_ids) + len(new_tracks)} треков"
            
            await session.commit()
            
            logger.info(f"Updated auto-album {playlist.name}: +{len(new_tracks)} tracks")
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
            "albums": []
        }
        
        candidates = await self.get_album_candidates(user_id)
        
        for candidate in candidates:
            artist = candidate["artist"]
            album = candidate["album"]
            deezer_album_id = candidate.get("deezer_album_id")
            cover_url = candidate.get("cover_url")
            
            # Check if playlist already exists
            existing = await self.check_existing_album_playlist(
                user_id, artist, album, deezer_album_id
            )
            
            # Get all tracks for this album
            tracks = await self.get_album_tracks(
                user_id, artist, album, deezer_album_id
            )
            
            if existing:
                # Update existing playlist
                updated = await self.update_album_playlist(
                    existing, tracks, deezer_album_id
                )
                if updated:
                    stats["updated"] += 1
                    stats["albums"].append({
                        "name": f"{artist} — {album}",
                        "action": "updated"
                    })
                else:
                    stats["skipped"] += 1
            else:
                # Create new playlist
                await self.create_album_playlist(
                    user_id=user_id,
                    artist=artist,
                    album=album,
                    tracks=tracks,
                    deezer_album_id=deezer_album_id,
                    cover_url=cover_url
                )
                stats["created"] += 1
                stats["albums"].append({
                    "name": f"{artist} — {album}",
                    "action": "created",
                    "track_count": len(tracks)
                })
        
        return stats


# Global instance
album_service = AlbumAssemblyService()

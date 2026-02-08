"""
TG Player - Album Assembly Service v2

Handles automatic and manual album grouping for tracks.
Uses new model structure with AlbumTrack association.
"""
import json
import logging
from typing import Optional, List, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass

from sqlalchemy import select, func, and_, delete
from sqlalchemy.orm import selectinload

from shared.database import get_session
from shared.models import (
    Track, TrackEnrichment, Album, AlbumTrack, UserLibrary, utcnow
)
from shared.matching import (
    normalize_artist, normalize_title, fuzzy_match_album,
    ALBUM_MATCH_THRESHOLD
)

logger = logging.getLogger(__name__)


# Alias for backward compatibility
def normalize_album(s: str) -> str:
    """Normalize album name for matching"""
    return normalize_title(s)


@dataclass
class AlbumCandidate:
    """Represents a potential album match for a track"""
    album_id: int
    album_name: str
    artist_name: str
    match_score: float
    track_count: int


class AlbumService:
    """Service for album assembly and management"""
    
    async def find_or_create_album(
        self,
        album_name: str,
        artist_name: str,
        cover_url: Optional[str] = None,
        release_date: Optional[str] = None,  # YYYY-MM-DD string
        deezer_album_id: Optional[int] = None,
        total_tracks: Optional[int] = None,
        full_tracklist: Optional[List[dict]] = None,  # Full album tracklist from Deezer
    ) -> int:
        """
        Find existing album or create new one.
        
        Uses fuzzy matching to avoid duplicate albums with slightly different names.
        
        Returns:
            Album ID
        """
        normalized_album = normalize_album(album_name)
        normalized_artist = normalize_artist(artist_name)
        
        async with get_session() as session:
            # Try to find by Deezer ID first (most reliable)
            if deezer_album_id:
                result = await session.execute(
                    select(Album)
                    .where(Album.deezer_album_id == deezer_album_id)
                )
                album = result.scalar_one_or_none()
                if album:
                    # Update with any new info
                    await self._update_album_if_needed(
                        album, cover_url, release_date, full_tracklist
                    )
                    return album.id
            
            # Search by normalized artist
            result = await session.execute(
                select(Album)
                .where(Album.normalized_artist == normalized_artist)
            )
            candidates = result.scalars().all()
            
            # Fuzzy match against candidates
            for candidate in candidates:
                if fuzzy_match_album(album_name, candidate.name) >= ALBUM_MATCH_THRESHOLD:
                    await self._update_album_if_needed(
                        candidate, cover_url, release_date, full_tracklist
                    )
                    if deezer_album_id and not candidate.deezer_album_id:
                        candidate.deezer_album_id = deezer_album_id
                    return candidate.id
            
            # Create new album
            album = Album(
                name=album_name,
                artist=artist_name,
                normalized_name=normalized_album,
                normalized_artist=normalized_artist,
                cover_url=cover_url,
                release_date=release_date,
                deezer_album_id=deezer_album_id,
                total_tracks=total_tracks,
                full_tracklist=json.dumps(full_tracklist) if full_tracklist else None,
            )
            session.add(album)
            await session.flush()
            
            logger.info(f"Created album: {album_name} by {artist_name} (ID: {album.id})")
            return album.id
    
    async def _update_album_if_needed(
        self,
        album: Album,
        cover_url: Optional[str],
        release_date: Optional[str],
        full_tracklist: Optional[List[dict]] = None,
    ):
        """Update album with new info if current is missing"""
        if cover_url and not album.cover_url:
            album.cover_url = cover_url
        if release_date and not album.release_date:
            album.release_date = release_date
        if full_tracklist and not album.full_tracklist:
            album.full_tracklist = json.dumps(full_tracklist)
        album.updated_at = utcnow()
    
    async def assign_track_to_album(
        self,
        track_id: int,
        album_id: int,
        track_number: Optional[int] = None,
    ):
        """
        Assign a track to an album.
        
        Args:
            track_id: Track ID
            album_id: Album ID
            track_number: Position in album (1-based)
        """
        async with get_session() as session:
            # Check if already assigned
            result = await session.execute(
                select(AlbumTrack).where(
                    and_(
                        AlbumTrack.track_id == track_id,
                        AlbumTrack.album_id == album_id,
                    )
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update track number if provided
                if track_number is not None and existing.track_number != track_number:
                    existing.track_number = track_number
                return
            
            # Create assignment
            album_track = AlbumTrack(
                track_id=track_id,
                album_id=album_id,
                track_number=track_number or 0,
            )
            session.add(album_track)
            
            logger.debug(f"Assigned track {track_id} to album {album_id}")
    
    async def remove_track_from_album(self, track_id: int, album_id: int):
        """Remove track from album"""
        async with get_session() as session:
            await session.execute(
                delete(AlbumTrack).where(
                    and_(
                        AlbumTrack.track_id == track_id,
                        AlbumTrack.album_id == album_id,
                    )
                )
            )
            
            # Check if album is now empty and delete if so
            remaining = await session.scalar(
                select(func.count(AlbumTrack.id))
                .where(AlbumTrack.album_id == album_id)
            )
            if remaining == 0:
                album = await session.get(Album, album_id)
                if album:
                    await session.delete(album)
                    logger.info(f"Deleted empty album {album_id}")
    
    async def auto_assign_album_from_enrichment(self, track_id: int) -> Optional[int]:
        """
        Automatically assign track to album based on enrichment data.
        Also loads full album tracklist from Deezer if available.
        
        Skips tracks without real metadata (placeholder titles) to avoid
        creating fake "unknown" albums.
        
        Returns:
            Album ID if assigned, None otherwise
        """
        async with get_session() as session:
            # Get track with enrichment
            result = await session.execute(
                select(Track)
                .options(selectinload(Track.enrichment))
                .where(Track.id == track_id)
            )
            track = result.scalar_one_or_none()
            
            if not track or not track.enrichment:
                return None
            
            enrichment = track.enrichment
            if not enrichment.album_name:
                return None
            
            # Skip tracks without real metadata - they shouldn't be in albums
            # This prevents "Без названия" tracks from being assigned to albums
            if not track.has_metadata:
                logger.debug(f"Skipping album assignment for track {track_id} - no real metadata")
                return None
            
            # Load full tracklist - Last.fm first (richer database), Deezer fallback
            full_tracklist = None
            total_tracks = None
            
            # Try Last.fm first (richer database, more albums)
            if track.artist:
                full_tracklist = await self._fetch_album_tracklist_lastfm(
                    album_name=enrichment.album_name,
                    artist_name=track.artist,
                )
            
            # Fallback to Deezer if Last.fm unavailable
            if not full_tracklist and enrichment.deezer_album_id:
                full_tracklist = await self._fetch_album_tracklist(enrichment.deezer_album_id)
            
            if full_tracklist:
                total_tracks = len(full_tracklist)
            
            # Find or create album
            album_id = await self.find_or_create_album(
                album_name=enrichment.album_name,
                artist_name=track.artist or "",
                cover_url=enrichment.cover_url,
                release_date=enrichment.release_date,
                deezer_album_id=enrichment.deezer_album_id,
                total_tracks=total_tracks,
                full_tracklist=full_tracklist,
            )
            
            # Assign track
            await self.assign_track_to_album(
                track_id=track_id,
                album_id=album_id,
                track_number=enrichment.track_number,
            )
            
            return album_id
    
    async def _fetch_album_tracklist(self, deezer_album_id: int) -> Optional[List[dict]]:
        """
        Fetch full album tracklist from Deezer.
        
        Returns list of track info dicts with:
        - track_number: position in album
        - title: track title
        - artist: artist name
        - duration: duration in seconds
        - deezer_id: Deezer track ID
        """
        try:
            from bot.services.enrichment.deezer import deezer_client
            
            tracks = await deezer_client.get_album_tracks(deezer_album_id)
            if not tracks:
                return None
            
            tracklist = []
            for i, t in enumerate(tracks, 1):
                tracklist.append({
                    "track_number": i,
                    "title": t.get("title", ""),
                    "artist": t.get("artist", {}).get("name", ""),
                    "duration": t.get("duration", 0),
                    "deezer_id": t.get("id"),
                })
            
            logger.info(f"Loaded tracklist for Deezer album {deezer_album_id}: {len(tracklist)} tracks")
            return tracklist
            
        except Exception as e:
            logger.error(f"Failed to fetch album tracklist: {e}")
            return None
    
    async def _fetch_album_tracklist_lastfm(
        self,
        album_name: str,
        artist_name: str,
    ) -> Optional[List[dict]]:
        """
        Fetch album tracklist from Last.fm (fallback when Deezer unavailable).
        
        Returns list of track info dicts with:
        - track_number: position in album
        - title: track title
        - artist: artist name
        - duration: duration in seconds
        """
        try:
            from bot.services.enrichment.lastfm import lastfm_client
            
            if not lastfm_client.is_configured:
                return None
            
            album_info = await lastfm_client.get_album_info(artist_name, album_name)
            if not album_info:
                return None
            
            tracks = album_info.get("tracks", [])
            if not tracks:
                return None
            
            tracklist = []
            for i, t in enumerate(tracks, 1):
                duration = 0
                if t.get("duration"):
                    try:
                        duration = int(t["duration"])
                    except (ValueError, TypeError):
                        pass
                
                tracklist.append({
                    "track_number": i,
                    "title": t.get("name", ""),
                    "artist": artist_name,
                    "duration": duration,
                })
            
            logger.info(f"Loaded tracklist from Last.fm: {album_name} - {len(tracklist)} tracks")
            return tracklist
            
        except Exception as e:
            logger.error(f"Failed to fetch Last.fm tracklist: {e}")
            return None
    
    async def find_album_candidates(
        self,
        album_name: str,
        artist_name: str,
        user_id: Optional[int] = None,
        limit: int = 5,
    ) -> List[AlbumCandidate]:
        """
        Find potential album matches for fuzzy search.
        
        Args:
            album_name: Album name to search
            artist_name: Artist name
            user_id: If provided, only albums with tracks in user's library
            limit: Max candidates to return
            
        Returns:
            List of album candidates sorted by match score
        """
        normalized_artist = normalize_artist(artist_name)
        
        async with get_session() as session:
            # Base query
            query = select(Album).where(
                Album.normalized_artist == normalized_artist
            )
            
            # If user_id provided, filter to albums with user's tracks
            if user_id:
                user_album_ids = (
                    select(AlbumTrack.album_id)
                    .distinct()
                    .join(UserLibrary, UserLibrary.track_id == AlbumTrack.track_id)
                    .where(UserLibrary.user_id == user_id)
                    .subquery()
                )
                query = query.where(Album.id.in_(select(user_album_ids)))
            
            result = await session.execute(query)
            albums = result.scalars().all()
            
            # Calculate fuzzy scores
            candidates = []
            for album in albums:
                score = fuzzy_match_album(album_name, album.name)
                if score >= ALBUM_MATCH_THRESHOLD * 0.8:  # Lower threshold for candidates
                    # Get track count
                    count_result = await session.execute(
                        select(func.count(AlbumTrack.id))
                        .where(AlbumTrack.album_id == album.id)
                    )
                    track_count = count_result.scalar() or 0
                    
                    candidates.append(AlbumCandidate(
                        album_id=album.id,
                        album_name=album.name,
                        artist_name=album.artist,
                        match_score=score,
                        track_count=track_count,
                    ))
            
            # Sort by score and limit
            candidates.sort(key=lambda x: x.match_score, reverse=True)
            return candidates[:limit]
    
    async def get_album_tracks(
        self,
        album_id: int,
        user_id: Optional[int] = None,
        order_by_track_number: bool = True,
    ) -> List[Track]:
        """
        Get tracks in an album.
        
        Args:
            album_id: Album ID
            user_id: If provided, only tracks in user's library
            order_by_track_number: Sort by track number
            
        Returns:
            List of tracks
        """
        async with get_session() as session:
            query = (
                select(Track)
                .join(AlbumTrack, AlbumTrack.track_id == Track.id)
                .where(AlbumTrack.album_id == album_id)
                .options(selectinload(Track.enrichment))
            )
            
            if user_id:
                query = query.join(
                    UserLibrary, UserLibrary.track_id == Track.id
                ).where(UserLibrary.user_id == user_id)
            
            if order_by_track_number:
                query = query.order_by(AlbumTrack.track_number.asc().nullslast())
            
            result = await session.execute(query)
            return list(result.scalars().unique().all())
    
    async def merge_albums(self, source_album_id: int, target_album_id: int) -> bool:
        """
        Merge source album into target album.
        
        All tracks from source are moved to target, then source is deleted.
        
        Returns:
            True if merge successful
        """
        async with get_session() as session:
            source = await session.get(Album, source_album_id)
            target = await session.get(Album, target_album_id)
            
            if not source or not target:
                return False
            
            # Get max track number in target
            max_num = await session.scalar(
                select(func.max(AlbumTrack.track_number))
                .where(AlbumTrack.album_id == target_album_id)
            ) or 0
            
            # Get tracks from source
            result = await session.execute(
                select(AlbumTrack)
                .where(AlbumTrack.album_id == source_album_id)
                .order_by(AlbumTrack.track_number)
            )
            source_tracks = result.scalars().all()
            
            # Move tracks to target
            for i, at in enumerate(source_tracks):
                # Check if track already in target
                existing = await session.scalar(
                    select(AlbumTrack)
                    .where(
                        AlbumTrack.album_id == target_album_id,
                        AlbumTrack.track_id == at.track_id
                    )
                )
                if not existing:
                    at.album_id = target_album_id
                    at.track_number = max_num + i + 1
                else:
                    # Already in target, just delete from source
                    await session.delete(at)
            
            # Delete source album
            await session.delete(source)
            
            logger.info(f"Merged album {source_album_id} into {target_album_id}")
            return True
    
    async def get_user_albums(
        self,
        user_id: int,
        artist_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Album], int]:
        """
        Get albums that have tracks in user's library.
        
        Returns:
            Tuple of (albums list, total count)
        """
        async with get_session() as session:
            # Subquery for user's album IDs
            user_album_ids = (
                select(AlbumTrack.album_id)
                .distinct()
                .join(UserLibrary, UserLibrary.track_id == AlbumTrack.track_id)
                .where(UserLibrary.user_id == user_id)
            )
            
            # Base query
            query = select(Album).where(Album.id.in_(user_album_ids))
            count_query = select(func.count(Album.id)).where(Album.id.in_(user_album_ids))
            
            # Artist filter
            if artist_filter:
                artist_lower = artist_filter.lower()
                query = query.where(func.lower(Album.artist) == artist_lower)
                count_query = count_query.where(func.lower(Album.artist) == artist_lower)
            
            # Get total
            total = await session.scalar(count_query) or 0
            
            # Pagination and ordering
            query = query.order_by(Album.artist, Album.name).offset(offset).limit(limit)
            
            result = await session.execute(query)
            albums = list(result.scalars().all())
            
            return albums, total


# Global instance
album_service = AlbumService()

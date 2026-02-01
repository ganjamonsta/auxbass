"""
TG Player - Deduplication Service

Service for finding and resolving duplicate tracks.
"""
import logging
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import get_session
from shared.models import Track, TrackEnrichment, UserLibrary
from shared.matching import normalize_unicode, generate_hashtags

logger = logging.getLogger(__name__)

class DeduplicationService:
    
    async def get_duplicate_stats(self, user_id: int) -> dict:
        """
        Analyze library and return statistics about duplicates.
        """
        async with get_session() as session:
            # 1. Total tracks in user library
            total_tracks = await session.scalar(
                select(func.count(UserLibrary.id)).where(UserLibrary.user_id == user_id)
            ) or 0
            
            # 2. Find duplicates by artist/title (content duplicates)
            # We work on Track level but filtered by UserLibrary
            
            # Fetch all tracks for user to memory (for 1600 tracks it's fine and faster than complex SQL grouping for fuzzy matching)
            # We need Track info
            result = await session.execute(
                select(Track)
                .join(UserLibrary)
                .where(UserLibrary.user_id == user_id)
                .options(selectinload(Track.enrichment))
            )
            tracks = result.scalars().all()
            
            content_groups = defaultdict(list)
            
            for track in tracks:
                # Normalize keys
                artist = normalize_unicode(track.artist or "").lower().strip()
                title = normalize_unicode(track.title or "").lower().strip()
                
                if artist and title:
                    key = f"{artist}|{title}"
                    content_groups[key].append(track)
            
            # Filter groups with > 1 track
            duplicate_groups = {k: v for k, v in content_groups.items() if len(v) > 1}
            potential_duplicates_count = sum(len(v) for v in duplicate_groups.values())
            groups_count = len(duplicate_groups)
            
            return {
                "total_tracks": total_tracks,
                "duplicate_groups_count": groups_count,
                "potential_duplicates_count": potential_duplicates_count,
                "groups": duplicate_groups # CAUTION: This might be large, we'll cache it or re-query in flow
            }

    async def get_next_duplicate_group(self, user_id: int, offset: int = 0) -> Optional[Tuple[str, List[Track]]]:
        """
        Get a specific group of duplicates for review.
        Returns (group_key, list_of_tracks)
        """
        stats = await self.get_duplicate_stats(user_id)
        groups = list(stats['groups'].items())
        
        if 0 <= offset < len(groups):
            return groups[offset]
        return None

    async def resolve_duplicates(self, keep_track_id: int, delete_track_ids: List[int], user_id: int) -> bool:
        """
        Keep one track and remove others from UserLibrary (and optionally delete Track if no other owners).
        """
        async with get_session() as session:
            # Delete from UserLibrary
            stmt = select(UserLibrary).where(
                UserLibrary.user_id == user_id,
                UserLibrary.track_id.in_(delete_track_ids)
            )
            entries = (await session.execute(stmt)).scalars().all()
            
            for entry in entries:
                await session.delete(entry)
                
            # Optional: Check if tracks are orphaned (no other library entries) and delete them
            # For now, let's strictly follow the user request: "remove duplicates"
            # If the user uploaded them, and no one else added them, maybe we should delete the Track?
            # Safe logic: Remove from Library. If Track.uploader is this user and no other library entries, delete Track.
            
            for tid in delete_track_ids:
                # Check if anyone else has this track
                other_usage = await session.scalar(
                    select(func.count(UserLibrary.id)).where(UserLibrary.track_id == tid)
                )
                
                # If we just deleted the entry, count should be 0 (if transaction not committed yet? Session tracks it)
                # Actually, wait, we 'await session.delete(entry)' but not committed.
                # SQLAlchemy session will know it's deleted.
                
                if other_usage == 0:
                     # Check if it's used in any playlists?
                     # Models show PlaylistTrack -> cascade delete if Track deleted?
                     # Let's verify Track model:
                     # playlist_tracks: Mapped[List["PlaylistTrack"]] = relationship(back_populates="track", cascade="all, delete-orphan")
                     # Yes.
                     
                     # Only delete actual Track if user is uploader or admin logic?
                     # Let's just remove from Library for safety, or Delete Track if explicitly asked.
                     # User said: "чтоб их послуушать можно было и уудалить какие внатуре дубликаты"
                     # Implies deleting the file/track entry.
                     
                     track = await session.get(Track, tid)
                     if track and track.uploader_id == user_id:
                         await session.delete(track)

            await session.commit()
            return True

deduplication_service = DeduplicationService()

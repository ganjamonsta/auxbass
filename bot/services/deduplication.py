"""
TG Player - Deduplication Service

Service for finding and resolving duplicate tracks.
"""
import logging
from typing import List, Optional, Tuple
from collections import defaultdict
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from shared.database import get_session
from shared.models import Track, UserLibrary, ChannelMessage, ChannelMessageStatus, UserChannel
from shared.matching import normalize_unicode

logger = logging.getLogger(__name__)


class UploadQualityDecision:
    """Result of comparing upload quality vs existing duplicates"""
    SAVE_AUTO = "save_auto"  # HD upgrade - save without asking
    ASK_USER = "ask_user"    # Same quality or downgrade - ask user
    NO_DUPLICATES = "no_duplicates"  # No duplicates found

# Threshold for quality difference detection
# If bitrate differs by more than this ratio, tracks are considered different quality versions
QUALITY_DIFF_THRESHOLD = 0.4  # 40% difference = different quality (e.g. MP3 128 vs FLAC)


def get_approx_bitrate(track: Track) -> Optional[float]:
    """
    Calculate approximate bitrate in kbps.
    Returns None if duration or file_size is not available.
    """
    return get_approx_bitrate_raw(track.duration, track.file_size)


def get_approx_bitrate_raw(duration: Optional[int], file_size: Optional[int]) -> Optional[float]:
    """
    Calculate approximate bitrate in kbps from raw values.
    Returns None if duration or file_size is not available.
    """
    if not duration or not file_size or duration == 0:
        return None
    return (file_size * 8) / duration / 1000


# Lossless audio MIME types (shared constant)
LOSSLESS_MIME_TYPES = frozenset({
    'audio/flac', 'audio/x-flac', 'audio/wav', 'audio/x-wav',
    'audio/alac', 'audio/x-alac', 'audio/aiff', 'audio/x-aiff'
})


def is_hd_quality_raw(duration: Optional[int], file_size: Optional[int], mime_type: Optional[str] = None) -> bool:
    """
    Check if track is likely an HD/lossless version from raw values.
    HD versions typically have:
    - Higher bitrate (> 500 kbps suggests lossless)
    - FLAC, WAV, ALAC mime types
    """
    if mime_type and mime_type.lower() in LOSSLESS_MIME_TYPES:
        return True
    
    bitrate = get_approx_bitrate_raw(duration, file_size)
    if bitrate and bitrate > 500:
        return True
    
    return False


def is_hd_version(track: Track) -> bool:
    """
    Check if track is likely an HD/lossless version.
    Delegates to is_hd_quality_raw with track fields.
    """
    return is_hd_quality_raw(track.duration, track.file_size, track.mime_type)


def are_same_quality_version(track1: Track, track2: Track) -> bool:
    """
    Check if two tracks are the same quality version.
    Returns True if they should be considered duplicates,
    False if one is HD version of the other.
    """
    bitrate1 = get_approx_bitrate(track1)
    bitrate2 = get_approx_bitrate(track2)
    
    # If we can't calculate bitrate for both, fallback to file size comparison
    if bitrate1 is None or bitrate2 is None:
        # Compare file sizes if available
        if track1.file_size and track2.file_size:
            size_ratio = max(track1.file_size, track2.file_size) / min(track1.file_size, track2.file_size)
            # If one file is 2x+ larger, they are different quality
            if size_ratio > 2.0:
                return False
        return True
    
    # Compare bitrates
    if bitrate1 == 0 or bitrate2 == 0:
        return True
        
    ratio = max(bitrate1, bitrate2) / min(bitrate1, bitrate2)
    # If bitrate differs by more than threshold, different quality
    if ratio > (1 + QUALITY_DIFF_THRESHOLD):
        return False
    
    return True


def split_by_quality(tracks: List[Track]) -> List[List[Track]]:
    """
    Split a group of potential duplicates into subgroups by quality.
    Each subgroup contains tracks of similar quality.
    
    Returns list of subgroups, where each subgroup has 2+ tracks (actual duplicates).
    """
    if len(tracks) <= 1:
        return []
    
    # Group by quality using union-find like approach
    quality_groups: List[List[Track]] = []
    
    for track in tracks:
        placed = False
        for group in quality_groups:
            # Check if track matches quality of first track in group
            if are_same_quality_version(track, group[0]):
                group.append(track)
                placed = True
                break
        
        if not placed:
            quality_groups.append([track])
    
    # Return only groups with 2+ tracks (actual duplicates)
    return [g for g in quality_groups if len(g) > 1]

class DeduplicationService:
    
    async def get_duplicate_stats(self, user_id: int) -> dict:
        """
        Analyze library and return statistics about duplicates.
        
        Note: Tracks with significantly different quality (HD vs regular) 
        are NOT considered duplicates - they are different versions.
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
            
            # Filter groups with > 1 track by same artist|title
            raw_duplicate_groups = {k: v for k, v in content_groups.items() if len(v) > 1}
            
            # Now split each group by quality to exclude HD versions from duplicates
            # HD version of a track should NOT be considered a duplicate
            duplicate_groups = {}
            for key, group_tracks in raw_duplicate_groups.items():
                quality_subgroups = split_by_quality(group_tracks)
                
                # Each quality subgroup is a set of actual duplicates
                for idx, subgroup in enumerate(quality_subgroups):
                    # Create unique key for each quality subgroup
                    if idx == 0:
                        subgroup_key = key
                    else:
                        subgroup_key = f"{key}|quality_{idx}"
                    duplicate_groups[subgroup_key] = subgroup
            
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

            return True

    async def delete_single_track(self, track_id: int, user_id: int) -> bool:
        """
        Delete a single track from user's library.
        If track has no other users, delete the Track entity as well.
        """
        async with get_session() as session:
            # Remove from UserLibrary
            stmt = select(UserLibrary).where(
                UserLibrary.user_id == user_id,
                UserLibrary.track_id == track_id
            )
            entry = (await session.execute(stmt)).scalar_one_or_none()
            
            if entry:
                await session.delete(entry)
            
            # Check if anyone else has this track
            other_usage = await session.scalar(
                select(func.count(UserLibrary.id)).where(UserLibrary.track_id == track_id)
            )
            
            if other_usage == 0:
                # No one else has this track, delete the Track entity
                track = await session.get(Track, track_id)
                if track and track.uploader_id == user_id:
                    await session.delete(track)
            
            return True

    async def find_potential_duplicates(
        self,
        user_id: int,
        artist: Optional[str],
        title: Optional[str],
        file_unique_id: str,
        limit: int = 5
    ) -> List[Track]:
        """
        Find tracks that might be duplicates of an incoming upload.
        Uses fuzzy matching on artist/title.
        Excludes the exact same file (by file_unique_id).
        
        Checks TWO sources:
          1. UserLibrary — tracks the user already has
          2. ChannelMessage(status=SENT) — tracks already in the user's channel
        
        This prevents re-uploading a track that is already forwarded
        to the channel even if the user deleted it from their library.
        
        Returns list of potential duplicate tracks.
        """
        if not artist and not title:
            return []
        
        norm_artist = normalize_unicode(artist or "").lower().strip()
        norm_title = normalize_unicode(title or "").lower().strip()
        
        if not norm_artist and not norm_title:
            return []
        
        async with get_session() as session:
            # 1) Tracks from UserLibrary
            lib_result = await session.execute(
                select(Track)
                .join(UserLibrary)
                .where(UserLibrary.user_id == user_id)
                .where(Track.file_unique_id != file_unique_id)
                .options(selectinload(Track.enrichment))
            )
            library_tracks = list(lib_result.scalars().all())
            
            # 2) Tracks already SENT to the user's channel (may not be in library)
            channel_result = await session.execute(
                select(Track)
                .join(ChannelMessage, ChannelMessage.track_id == Track.id)
                .join(UserChannel, UserChannel.id == ChannelMessage.channel_id)
                .where(
                    UserChannel.user_id == user_id,
                    UserChannel.is_active == True,
                    ChannelMessage.status == ChannelMessageStatus.SENT,
                    Track.file_unique_id != file_unique_id,
                )
                .options(selectinload(Track.enrichment))
            )
            channel_tracks = list(channel_result.scalars().all())
            
            # Merge, deduplicate by track id
            seen_ids = set()
            tracks: List[Track] = []
            for t in library_tracks + channel_tracks:
                if t.id not in seen_ids:
                    seen_ids.add(t.id)
                    tracks.append(t)
            
            # Find matches by normalized artist+title
            matches = []
            for track in tracks:
                track_artist = normalize_unicode(track.artist or "").lower().strip()
                track_title = normalize_unicode(track.title or "").lower().strip()
                
                # Check for exact or near match
                if norm_artist and norm_title:
                    # Both must match
                    if track_artist == norm_artist and track_title == norm_title:
                        matches.append((track, 1.0))  # Exact match
                    elif track_artist and track_title:
                        # Fuzzy check: artist matches AND title contains or matches
                        artist_match = track_artist == norm_artist or norm_artist in track_artist or track_artist in norm_artist
                        title_match = track_title == norm_title or norm_title in track_title or track_title in norm_title
                        if artist_match and title_match:
                            matches.append((track, 0.8))
                elif norm_title and track_title == norm_title:
                    # Only title available and matches
                    matches.append((track, 0.7))
            
            # Sort by match score and return top matches
            matches.sort(key=lambda x: x[1], reverse=True)
            return [m[0] for m in matches[:limit]]


deduplication_service = DeduplicationService()

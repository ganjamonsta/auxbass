"""
TG Player - Auto Album Assembly Service
Automatically creates playlists from tracks with matching album/artist
"""
import logging
import re
import unicodedata
from typing import Optional, List, Dict, Tuple
from sqlalchemy import select, func, delete

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import get_session
from shared.models import Track, Playlist, PlaylistTrack, UserLibrary
from .metadata import metadata_service

logger = logging.getLogger(__name__)


def normalize_artist_for_grouping(artist: str) -> str:
    """
    Normalize artist name for album grouping.
    Takes first artist, removes feat./prod., normalizes case.
    """
    if not artist:
        return ""
    
    artist = artist.lower()
    
    # Remove content in parentheses
    artist = re.sub(r'\s*[\(\[].*?[\)\]]', '', artist)
    
    # Remove feat., ft., prod., etc. and everything after
    artist = re.sub(r'\s*(feat\.?|ft\.?|featuring|vs\.?|prod\.?|produced\s+by)\s+.*', '', artist, flags=re.IGNORECASE)
    
    # Take first artist from list
    artist = re.split(r'\s*[,&+]\s*|\s+(?:x|and|with)\s+', artist, flags=re.IGNORECASE)[0]
    
    # Replace $ with s, remove special chars
    artist = artist.replace('$', 's')
    artist = re.sub(r'[^\w\s]', '', artist)
    
    # Normalize whitespace
    artist = ' '.join(artist.split())
    
    return artist.strip()


def normalize_album_name(album: str) -> str:
    """
    Normalize album name for comparison/grouping.
    PRESERVES important suffixes like (Deluxe), (Remastered), etc.
    
    Examples:
    - "D&G" -> "dg"
    - "D & G" -> "dg"  
    - "Warlord (Deluxe)" -> "warlord deluxe"
    - " ICEDANCER " -> "icedancer"
    """
    if not album:
        return ""
    
    # Normalize unicode
    album = unicodedata.normalize('NFKD', album)
    album = album.lower().strip()
    
    # Extract important suffixes BEFORE cleaning
    # These make albums distinct (Deluxe vs regular)
    important_suffixes = []
    suffix_patterns = [
        r'\(deluxe[^)]*\)',
        r'\(remaster(?:ed)?[^)]*\)',
        r'\(expanded[^)]*\)',
        r'\(anniversary[^)]*\)',
        r'\(bonus[^)]*\)',
        r'\[deluxe[^\]]*\]',
        r'\[remaster(?:ed)?[^\]]*\]',
    ]
    for pattern in suffix_patterns:
        match = re.search(pattern, album, re.IGNORECASE)
        if match:
            # Extract just the key word
            suffix = re.sub(r'[\(\)\[\]]', '', match.group()).strip()
            suffix = suffix.split()[0]  # Take first word: "deluxe edition" -> "deluxe"
            important_suffixes.append(suffix)
    
    # Remove ALL content in parentheses/brackets for base comparison
    album = re.sub(r'\s*[\(\[][^\)\]]*[\)\]]', '', album)
    
    # Replace & with nothing (D&G = DG)
    album = album.replace('&', '')
    album = album.replace('$', 's')
    
    # Remove special characters but keep letters and numbers
    album = re.sub(r'[^\w\s]', '', album)
    
    # Normalize whitespace
    album = ' '.join(album.split())
    
    # Add back important suffixes
    if important_suffixes:
        album = album + ' ' + ' '.join(sorted(important_suffixes))
    
    return album.strip()


def normalize_title(title: str) -> str:
    """
    Normalize track title for comparison.
    - Convert to lowercase
    - Remove content in parentheses (feat., remix, mix, etc.)
    - Remove special characters and extra spaces
    - Normalize unicode characters
    """
    if not title:
        return ""
    
    # Normalize unicode (e.g., curly apostrophes -> straight)
    title = unicodedata.normalize('NFKD', title)
    
    # Convert to lowercase
    title = title.lower()
    
    # Remove content in parentheses (often contains feat., remix, mix, etc.)
    title = re.sub(r'\s*\([^)]*\)', '', title)
    title = re.sub(r'\s*\[[^\]]*\]', '', title)
    
    # Remove "feat." / "ft." and everything after
    title = re.sub(r'\s*(feat\.?|ft\.?)\s+.*$', '', title, flags=re.IGNORECASE)
    
    # Replace special apostrophes with regular ones, then remove them
    title = title.replace("'", "'").replace("'", "'").replace("`", "'")
    title = title.replace("'", "")  # Remove apostrophes completely for matching
    
    # Remove special characters but keep letters, numbers, spaces
    title = re.sub(r"[^\w\s]", '', title)
    
    # Normalize spaces
    title = ' '.join(title.split())
    
    return title.strip()


def fuzzy_match_title(title1: str, title2: str) -> float:
    """
    Calculate similarity between two titles (0.0 to 1.0).
    Uses normalized comparison and partial matching.
    """
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    
    if not norm1 or not norm2:
        return 0.0
    
    # Exact match after normalization
    if norm1 == norm2:
        return 1.0
    
    # Compare without spaces (for cases like "cartier god" vs "cartiergod")
    compact1 = norm1.replace(" ", "")
    compact2 = norm2.replace(" ", "")
    
    if compact1 == compact2:
        return 1.0
    
    # One contains the other (for cases like "SmartWater" vs "Smartwater")
    if norm1 in norm2 or norm2 in norm1:
        return 0.9
    
    # Check compact versions
    if compact1 in compact2 or compact2 in compact1:
        return 0.85
    
    # Word-based comparison
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if not words1 or not words2:
        return 0.0
    
    # Jaccard similarity of words
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    if union == 0:
        return 0.0
    
    jaccard = intersection / union
    
    # Bonus for matching significant words (longer than 3 chars)
    significant1 = {w for w in words1 if len(w) > 3}
    significant2 = {w for w in words2 if len(w) > 3}
    
    if significant1 and significant2:
        sig_intersection = len(significant1 & significant2)
        sig_union = len(significant1 | significant2)
        if sig_union > 0:
            sig_jaccard = sig_intersection / sig_union
            # Weight significant words more heavily
            jaccard = max(jaccard, sig_jaccard * 0.95)
    
    return jaccard


def find_best_match(track_title: str, deezer_tracks: List[Dict], threshold: float = 0.6) -> Optional[int]:
    """
    Find the best matching Deezer track position for a given track title.
    Returns the position if a match is found above threshold, else None.
    """
    best_score = 0.0
    best_position = None
    
    for dt in deezer_tracks:
        deezer_title = dt.get("title", "")
        if not deezer_title:
            continue
        
        score = fuzzy_match_title(track_title, deezer_title)
        
        if score > best_score:
            best_score = score
            best_position = dt.get("position")
    
    if best_score >= threshold:
        return best_position
    
    return None


class AlbumAssemblyService:
    """Service for automatically assembling albums from user's tracks"""
    
    # Minimum tracks to consider as album (1 = allow singles)
    MIN_TRACKS_FOR_ALBUM = 1
    
    async def get_album_candidates(self, user_id: int) -> List[Dict]:
        """
        Find potential albums from user's tracks using smart two-phase grouping.
        
        Phase 1: Group by deezer_album_id (most reliable for compilations)
        Phase 2: Merge groups without deezer_album_id into groups that have it,
                 if the normalized album name matches
        
        This handles cases like:
        - Some tracks of D&G have deezer_album_id, some don't -> merged into one
        - Different artist spellings (BLADEE vs bladee) -> same album
        - Collaborations with different artists per track -> one album
        
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
            
            if not tracks:
                return []
            
            # ===== PHASE 1: Initial grouping =====
            # Group by deezer_album_id OR by normalized album name
            albums: Dict[str, Dict] = {}
            
            # Track which normalized album names have deezer_album_id
            # Key: normalized_album_name -> deezer_album_id (if any)
            album_name_to_deezer_id: Dict[str, int] = {}
            
            for track in tracks:
                album_norm = normalize_album_name(track.album)
                
                # Remember deezer_album_id for this album name
                if track.deezer_album_id and album_norm:
                    if album_norm not in album_name_to_deezer_id:
                        album_name_to_deezer_id[album_norm] = track.deezer_album_id
            
            # Now group tracks - prefer deezer_album_id, but use lookup
            for track in tracks:
                album_norm = normalize_album_name(track.album)
                
                # Determine the grouping key
                if track.deezer_album_id:
                    # Has deezer_album_id - use it
                    key = f"deezer:{track.deezer_album_id}"
                    effective_deezer_id = track.deezer_album_id
                elif album_norm in album_name_to_deezer_id:
                    # Doesn't have deezer_album_id, but another track with same 
                    # album name does - merge into that group!
                    effective_deezer_id = album_name_to_deezer_id[album_norm]
                    key = f"deezer:{effective_deezer_id}"
                else:
                    # No deezer_album_id anywhere - group by album name only
                    # (NOT by artist - albums can have multiple artists)
                    key = f"album:{album_norm}"
                    effective_deezer_id = None
                
                if key not in albums:
                    albums[key] = {
                        "album": track.album,  # Original name (first seen)
                        "album_norm": album_norm,
                        "deezer_album_id": effective_deezer_id,
                        "cover_url": track.cover_url,
                        "artists": set(),
                        "track_ids": set(),
                        "total_duration": 0,
                    }
                
                album_data = albums[key]
                
                # Collect all artists (original names for display)
                if track.artist:
                    album_data["artists"].add(track.artist)
                
                # Track unique tracks
                album_data["track_ids"].add(track.id)
                album_data["total_duration"] += track.duration or 0
                
                # Update cover_url if we don't have one (prefer enriched)
                if track.cover_url:
                    if not album_data["cover_url"]:
                        album_data["cover_url"] = track.cover_url
                    elif 'dzcdn.net' in track.cover_url and 'dzcdn.net' not in album_data["cover_url"]:
                        # Prefer Deezer covers
                        album_data["cover_url"] = track.cover_url
                
                # Update deezer_album_id if we don't have one
                if track.deezer_album_id and not album_data["deezer_album_id"]:
                    album_data["deezer_album_id"] = track.deezer_album_id
            
            # ===== PHASE 2: Merge remaining duplicates by normalized name =====
            # This catches cases where tracks have DIFFERENT deezer_album_ids 
            # but same album name (rare, but possible with remasters/re-releases)
            # We'll keep them separate for now - deezer_album_id is authoritative
            
            # ===== PHASE 3: Build candidate list =====
            candidates = []
            for key, data in albums.items():
                if len(data["track_ids"]) < self.MIN_TRACKS_FOR_ALBUM:
                    continue
                
                # Determine main artist (most common among tracks)
                artists_list = list(data["artists"])
                if artists_list:
                    # Normalize and count
                    artist_counts: Dict[str, int] = {}
                    for a in artists_list:
                        norm = normalize_artist_for_grouping(a)
                        artist_counts[norm] = artist_counts.get(norm, 0) + 1
                    
                    # Find most common normalized artist
                    most_common_norm = max(artist_counts, key=artist_counts.get)
                    
                    # Get original form of most common artist
                    main_artist = next(
                        (a for a in artists_list if normalize_artist_for_grouping(a) == most_common_norm),
                        artists_list[0]
                    )
                    
                    # Sort artists for consistent display
                    artists_list = sorted(set(artists_list))
                else:
                    main_artist = "Unknown"
                    artists_list = []
                
                candidates.append({
                    "artist": main_artist,
                    "all_artists": artists_list,
                    "album": data["album"],
                    "album_norm": data["album_norm"],
                    "deezer_album_id": data["deezer_album_id"],
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
        artist: str = "",
        deezer_album_id: Optional[int] = None,
        album_norm: Optional[str] = None
    ) -> Optional[Playlist]:
        """
        Check if auto-album playlist already exists for this album.
        Uses smart matching:
        1. By deezer_album_id (most reliable)
        2. By normalized album name (handles D&G vs D & G, etc.)
        
        Returns existing playlist or None.
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
            
            if not playlists:
                return None
            
            # First: try exact match by deezer_album_id (most reliable)
            if deezer_album_id:
                for pl in playlists:
                    if pl.deezer_album_id == deezer_album_id:
                        return pl
            
            # Prepare normalized album name for matching
            album_norm = album_norm or normalize_album_name(album)
            
            # Second: match by NORMALIZED album name
            for pl in playlists:
                if not pl.name:
                    continue
                
                # Normalize playlist name for comparison
                pl_album_norm = normalize_album_name(pl.name)
                
                if pl_album_norm == album_norm:
                    return pl
            
            return None
    
    async def find_duplicate_album_playlists(
        self, 
        user_id: int
    ) -> List[List[Playlist]]:
        """
        Find groups of duplicate album playlists for a user.
        Returns list of groups, where each group contains playlists 
        that should be merged.
        """
        async with get_session() as session:
            result = await session.execute(
                select(Playlist).where(
                    Playlist.user_id == user_id,
                    Playlist.is_auto_album == True,
                )
            )
            playlists = list(result.scalars().all())
            
            if len(playlists) < 2:
                return []
            
            # Group by normalized album name and deezer_album_id
            groups: Dict[str, List[Playlist]] = {}
            
            for pl in playlists:
                # Generate key similar to track grouping
                album_norm = normalize_album_name(pl.name) if pl.name else ""
                
                if pl.deezer_album_id:
                    key = f"deezer:{pl.deezer_album_id}"
                else:
                    key = f"album:{album_norm}"
                
                if key not in groups:
                    groups[key] = []
                groups[key].append(pl)
            
            # Return only groups with duplicates
            return [g for g in groups.values() if len(g) > 1]
    
    async def merge_duplicate_playlists(
        self,
        playlists: List[Playlist]
    ) -> Optional[Playlist]:
        """
        Merge multiple duplicate playlists into one.
        Keeps the playlist with best metadata (deezer_album_id, cover_url).
        Moves all tracks to the survivor, removes duplicates.
        """
        if len(playlists) < 2:
            return playlists[0] if playlists else None
        
        async with get_session() as session:
            # Re-fetch playlists in this session
            playlists = [await session.merge(pl) for pl in playlists]
            
            # Score each playlist to find the best one
            def score_playlist(pl: Playlist) -> int:
                return (
                    (100 if pl.deezer_album_id else 0) +
                    (50 if pl.cover_url and 'dzcdn.net' in pl.cover_url else 0) +
                    (10 if pl.cover_url else 0) +
                    (5 if pl.release_date else 0)
                )
            
            # Sort by score descending
            playlists.sort(key=score_playlist, reverse=True)
            survivor = playlists[0]
            to_merge = playlists[1:]
            
            logger.info(f"Merging {len(to_merge)} duplicate playlists into '{survivor.name}' (id={survivor.id})")
            
            # Get all track IDs from survivor
            result = await session.execute(
                select(PlaylistTrack.track_id)
                .where(PlaylistTrack.playlist_id == survivor.id)
            )
            survivor_track_ids = {row[0] for row in result.all()}
            
            # Get max position in survivor
            max_pos = await session.scalar(
                select(func.max(PlaylistTrack.position))
                .where(PlaylistTrack.playlist_id == survivor.id)
            ) or 0
            
            # Merge tracks from other playlists
            added_count = 0
            for pl in to_merge:
                result = await session.execute(
                    select(PlaylistTrack)
                    .where(PlaylistTrack.playlist_id == pl.id)
                )
                tracks = result.scalars().all()
                
                for pt in tracks:
                    if pt.track_id not in survivor_track_ids:
                        # Move track to survivor
                        max_pos += 1
                        new_pt = PlaylistTrack(
                            playlist_id=survivor.id,
                            track_id=pt.track_id,
                            position=max_pos
                        )
                        session.add(new_pt)
                        survivor_track_ids.add(pt.track_id)
                        added_count += 1
                
                # Delete tracks from old playlist
                await session.execute(
                    delete(PlaylistTrack).where(PlaylistTrack.playlist_id == pl.id)
                )
                
                # Delete the duplicate playlist
                await session.delete(pl)
            
            # Update survivor metadata from merged playlists if better
            for pl in to_merge:
                if not survivor.deezer_album_id and pl.deezer_album_id:
                    survivor.deezer_album_id = pl.deezer_album_id
                if not survivor.cover_url and pl.cover_url:
                    survivor.cover_url = pl.cover_url
                if not survivor.release_date and pl.release_date:
                    survivor.release_date = pl.release_date
            
            # Update description
            total = len(survivor_track_ids)
            survivor.description = f"Автоальбом • {total} треков"
            
            await session.commit()
            
            logger.info(f"Merged: kept '{survivor.name}', added {added_count} tracks, total {total}")
            return survivor
    
    async def get_album_tracks(
        self, 
        user_id: int, 
        album: str,
        artist: str = "",
        deezer_album_id: Optional[int] = None,
        album_norm: Optional[str] = None
    ) -> List[Track]:
        """
        Get all user's tracks for a specific album.
        Uses smart matching:
        1. By deezer_album_id (most reliable, handles compilations)
        2. By normalized album name (handles D&G vs D & G, etc.)
        
        Does NOT require artist match - albums can have multiple artists (compilations).
        Deduplicates by title to avoid duplicate tracks from different sources.
        """
        album_norm = album_norm or normalize_album_name(album)
        
        async with get_session() as session:
            # Get all tracks from user's library with album info
            result = await session.execute(
                select(Track)
                .join(UserLibrary, UserLibrary.track_id == Track.id)
                .where(
                    UserLibrary.user_id == user_id,
                    Track.album.isnot(None),
                    Track.album != ""
                )
            )
            
            # Filter by deezer_album_id OR normalized album name
            all_tracks = []
            for t in result.scalars().all():
                track_album_norm = normalize_album_name(t.album) if t.album else ""
                
                # Match by deezer_album_id (primary) or normalized album name
                if deezer_album_id:
                    # If we're looking for a specific deezer_album_id:
                    # - Include tracks WITH that deezer_album_id
                    # - Also include tracks WITHOUT deezer_album_id but with matching album name
                    if t.deezer_album_id == deezer_album_id:
                        all_tracks.append(t)
                    elif not t.deezer_album_id and track_album_norm == album_norm:
                        all_tracks.append(t)
                else:
                    # No deezer_album_id - match by normalized album name only
                    if track_album_norm == album_norm:
                        all_tracks.append(t)
            
            # Deduplicate by title using normalized matching
            # Keep the track with cover_url or higher quality metadata
            unique_tracks = []
            
            def is_duplicate(track: Track, existing_tracks: List[Track]) -> Optional[int]:
                """Check if track is duplicate of any existing track. Returns index if duplicate."""
                track_title_norm = normalize_title(track.title) if track.title else ""
                if not track_title_norm:
                    return None
                
                for i, existing in enumerate(existing_tracks):
                    existing_title_norm = normalize_title(existing.title) if existing.title else ""
                    if not existing_title_norm:
                        continue
                    
                    # Exact match after normalization
                    if track_title_norm == existing_title_norm:
                        return i
                    
                    # Fuzzy match (very high threshold to avoid false positives)
                    if fuzzy_match_title(track.title, existing.title) >= 0.9:
                        return i
                
                return None
            
            for track in all_tracks:
                dup_idx = is_duplicate(track, unique_tracks)
                if dup_idx is None:
                    # Not a duplicate, add it
                    unique_tracks.append(track)
                else:
                    # Duplicate found - prefer track with better metadata
                    existing = unique_tracks[dup_idx]
                    # Prefer: has cover > has deezer_album_id > has duration
                    existing_score = (
                        (1 if existing.cover_url else 0) * 100 +
                        (1 if existing.deezer_album_id else 0) * 10 +
                        (1 if existing.duration else 0)
                    )
                    track_score = (
                        (1 if track.cover_url else 0) * 100 +
                        (1 if track.deezer_album_id else 0) * 10 +
                        (1 if track.duration else 0)
                    )
                    if track_score > existing_score:
                        unique_tracks[dup_idx] = track
            
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
            # Get release date from Deezer if we have album ID
            release_date = None
            if deezer_album_id:
                release_date = await metadata_service.get_album_release_date(deezer_album_id)
            
            # If no Deezer album ID, try to get release date from Last.fm
            if not release_date and artist and album:
                from shared.config import get_settings
                settings = get_settings()
                if settings.lastfm_api_key:
                    release_date = await metadata_service._get_lastfm_album_release_date(
                        artist, album, settings.lastfm_api_key, 
                        await metadata_service._get_session()
                    )
            
            # Store album name only, artist is separate
            playlist = Playlist(
                user_id=user_id,
                name=album,  # Just album name
                album_artist=artist,  # Artist stored separately
                description=f"Автоальбом • {len(tracks)} треков",
                is_auto_album=True,
                deezer_album_id=deezer_album_id,
                cover_url=cover_url,
                release_date=release_date,
            )
            session.add(playlist)
            await session.flush()
            
            # Try to get correct track order from Deezer
            track_order = {}
            deezer_tracks_list = None
            if deezer_album_id:
                deezer_tracks_list = await self.get_deezer_album_tracklist(deezer_album_id)
                if deezer_tracks_list:
                    # Create mapping: lowercase title -> position (for exact match)
                    for dt in deezer_tracks_list:
                        if dt.get("title"):
                            track_order[dt["title"].lower()] = dt["position"]
            
            # Sort tracks by Deezer order or alphabetically
            def get_position(track):
                if track.title:
                    # Try exact match first
                    pos = track_order.get(track.title.lower())
                    if pos:
                        return (0, pos)  # Has exact Deezer position
                    
                    # Try fuzzy match if we have Deezer tracks
                    if deezer_tracks_list:
                        fuzzy_pos = find_best_match(track.title, deezer_tracks_list)
                        if fuzzy_pos:
                            return (0, fuzzy_pos)  # Has fuzzy Deezer position
                    
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
        If reorder=True or new tracks are added with Deezer data available,
        reorders all tracks according to Deezer tracklist.
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
            
            # Update release_date if not set
            release_date_updated = False
            if not playlist.release_date:
                # Try Deezer first
                if deezer_album_id or playlist.deezer_album_id:
                    album_id = deezer_album_id or playlist.deezer_album_id
                    release_date = await metadata_service.get_album_release_date(album_id)
                    if release_date:
                        playlist.release_date = release_date
                        release_date_updated = True
                
                # If still no release date, try Last.fm
                if not release_date_updated and playlist.album_artist and playlist.name:
                    from shared.config import get_settings
                    settings = get_settings()
                    if settings.lastfm_api_key:
                        release_date = await metadata_service._get_lastfm_album_release_date(
                            playlist.album_artist, playlist.name, settings.lastfm_api_key,
                            await metadata_service._get_session()
                        )
                        if release_date:
                            playlist.release_date = release_date
                            release_date_updated = True
            
            # Get existing track IDs in playlist
            result = await session.execute(
                select(PlaylistTrack.track_id)
                .where(PlaylistTrack.playlist_id == playlist.id)
            )
            existing_track_ids = {row[0] for row in result.all()}
            
            # Find new tracks (not already in playlist)
            new_tracks = [t for t in tracks if t.id not in existing_track_ids]
            
            if not new_tracks and not cover_updated and not reorder:
                return False
            
            # Get Deezer track order for smart insertion
            track_order = {}
            deezer_tracks_list = None
            album_id = deezer_album_id or playlist.deezer_album_id
            if album_id:
                deezer_tracks_list = await self.get_deezer_album_tracklist(album_id)
                if deezer_tracks_list:
                    for dt in deezer_tracks_list:
                        if dt.get("title"):
                            track_order[dt["title"].lower().strip()] = dt["position"]
            
            def get_deezer_position(track) -> Optional[int]:
                """Get Deezer position for a track (1-based), or None if not found."""
                if not track.title:
                    return None
                
                # Try exact match first
                pos = track_order.get(track.title.lower().strip())
                if pos:
                    return pos
                
                # Try fuzzy match if we have Deezer tracks
                if deezer_tracks_list:
                    fuzzy_pos = find_best_match(track.title, deezer_tracks_list)
                    if fuzzy_pos:
                        return fuzzy_pos
                
                return None
            
            # If we have Deezer data or explicit reorder, rebuild entire playlist with correct order
            should_reorder = reorder or (new_tracks and deezer_tracks_list)
            
            if should_reorder and deezer_tracks_list:
                # Delete all existing playlist tracks
                await session.execute(
                    delete(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist.id)
                )
                
                # Sort all tracks by Deezer order
                def get_sort_key(track):
                    pos = get_deezer_position(track)
                    if pos:
                        return (0, pos)  # Has Deezer position
                    return (1, track.title or "")  # Fallback to alphabetical at end
                
                sorted_tracks = sorted(tracks, key=get_sort_key)
                
                # Add all tracks with correct positions
                for position, track in enumerate(sorted_tracks, start=1):
                    pt = PlaylistTrack(
                        playlist_id=playlist.id,
                        track_id=track.id,
                        position=position
                    )
                    session.add(pt)
                
                added_count = len(new_tracks)
            else:
                # No Deezer data - just add new tracks at end
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
                
                added_count = len(new_tracks)
            
            # Update description
            total_tracks = len(tracks) if should_reorder else len(existing_track_ids) + len(new_tracks)
            playlist.description = f"Автоальбом • {total_tracks} треков"
            
            await session.commit()
            
            if should_reorder:
                action = f"reordered ({added_count} new)" if added_count else "reordered"
            else:
                action = f"+{added_count} tracks"
            logger.info(f"Updated auto-album {playlist.name}: {action}")
            return True
    
    async def assemble_albums_for_user(self, user_id: int) -> Dict:
        """
        Main method: find and create/update all album playlists for user.
        
        Steps:
        1. Clean up empty album playlists
        2. Merge duplicate playlists (D&G + D & G -> D&G)
        3. Find album candidates from tracks
        4. Create or update playlists
        
        Returns stats about created/updated/merged albums.
        """
        stats = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "merged": 0,
            "cleaned": 0,
            "albums": []
        }
        
        # Step 1: Clean up empty album playlists
        cleaned = await self._cleanup_empty_albums(user_id)
        stats["cleaned"] = cleaned
        
        # Step 2: Merge duplicate playlists BEFORE processing candidates
        duplicate_groups = await self.find_duplicate_album_playlists(user_id)
        for group in duplicate_groups:
            await self.merge_duplicate_playlists(group)
            stats["merged"] += len(group) - 1  # Count merged (not the survivor)
        
        # Step 3: Get album candidates
        candidates = await self.get_album_candidates(user_id)
        
        for candidate in candidates:
            album = candidate["album"]
            album_norm = candidate.get("album_norm")
            deezer_album_id = candidate.get("deezer_album_id")
            cover_url = candidate.get("cover_url")
            all_artists = candidate.get("all_artists", [candidate.get("artist", "Unknown")])
            main_artist = candidate.get("artist", "Unknown")
            
            # Format artist display name
            if len(all_artists) > 2:
                artist_display = f"{all_artists[0]} и др."
            elif len(all_artists) == 2:
                artist_display = " & ".join(all_artists)
            else:
                artist_display = all_artists[0] if all_artists else "Unknown"
            
            # Check if playlist already exists (using smart matching)
            existing = await self.check_existing_album_playlist(
                user_id, album, main_artist, deezer_album_id, album_norm
            )
            
            # Get all tracks for this album (using smart matching)
            tracks = await self.get_album_tracks(
                user_id, album, main_artist, deezer_album_id, album_norm
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

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
        Find potential albums from user's tracks.
        Groups by (normalized album name + normalized main artist) as key.
        This ensures tracks from different sources with same album/artist 
        are grouped together, while albums with same name but different artists
        remain separate.
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
            
            # Group by (normalized album + normalized artist) to:
            # 1. Merge tracks from same album with slight artist name variations
            # 2. Keep albums with same name but different artists separate
            albums: Dict[str, Dict] = {}
            
            for track in tracks:
                # Normalize album name and main artist for grouping key
                album_key = track.album.lower().strip()
                artist_key = normalize_artist_for_grouping(track.artist) if track.artist else ""
                
                # Combined key: album + normalized artist
                key = f"{album_key}||{artist_key}"
                
                if key not in albums:
                    albums[key] = {
                        "album": track.album,
                        "album_key": album_key,
                        "artist_key": artist_key,
                        "deezer_album_ids": set(),  # Collect all deezer IDs
                        "cover_url": track.cover_url,
                        "artists": set(),
                        "track_ids": set(),
                        "total_duration": 0,
                    }
                
                album_data = albums[key]
                
                # Collect all artists (original names)
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
        artist: str = "",
        deezer_album_id: Optional[int] = None
    ) -> Optional[Playlist]:
        """
        Check if auto-album playlist already exists for this album.
        Searches by album name and optionally artist.
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
            artist_key = normalize_artist_for_grouping(artist) if artist else ""
            
            for pl in playlists:
                if not pl.name:
                    continue
                    
                name_lower = pl.name.lower().strip()
                pl_artist_key = normalize_artist_for_grouping(pl.album_artist) if pl.album_artist else ""
                
                # Check album name match
                album_matches = (
                    name_lower == album_lower or
                    name_lower.endswith(f" — {album_lower}") or
                    (" — " in pl.name and pl.name.split(" — ", 1)[1].lower().strip() == album_lower)
                )
                
                if not album_matches:
                    continue
                
                # If we have artist info, also check artist match
                if artist_key and pl_artist_key:
                    # Artists must match
                    if artist_key == pl_artist_key or artist_key in pl_artist_key or pl_artist_key in artist_key:
                        return pl
                else:
                    # No artist info - just album match is enough
                    return pl
            
            return None
    
    async def get_album_tracks(
        self, 
        user_id: int, 
        album: str,
        artist: str = "",
        deezer_album_id: Optional[int] = None
    ) -> List[Track]:
        """
        Get all user's tracks for a specific album.
        Groups by album name and artist (normalized) to ensure correct grouping.
        Deduplicates by title to avoid duplicate tracks from different sources.
        """
        album_lower = album.lower().strip()
        artist_key = normalize_artist_for_grouping(artist) if artist else ""
        
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
            
            # Filter by album name and artist in Python
            all_tracks = []
            for t in result.scalars().all():
                if not t.album or t.album.lower().strip() != album_lower:
                    continue
                
                # If we have artist filter, check it matches
                if artist_key:
                    track_artist_key = normalize_artist_for_grouping(t.artist) if t.artist else ""
                    if track_artist_key != artist_key:
                        continue
                
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
                    # Prefer: has cover > has deezer_id > has duration
                    existing_score = (
                        (1 if existing.cover_url else 0) * 100 +
                        (1 if existing.deezer_id else 0) * 10 +
                        (1 if existing.duration else 0)
                    )
                    track_score = (
                        (1 if track.cover_url else 0) * 100 +
                        (1 if track.deezer_id else 0) * 10 +
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
            
            # Update release_date if not set and we have deezer_album_id
            release_date_updated = False
            if not playlist.release_date and (deezer_album_id or playlist.deezer_album_id):
                album_id = deezer_album_id or playlist.deezer_album_id
                release_date = await metadata_service.get_album_release_date(album_id)
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
            main_artist = candidate.get("artist", "Unknown")
            
            # Format artist display name
            if len(all_artists) > 2:
                artist_display = f"{all_artists[0]} и др."
            elif len(all_artists) == 2:
                artist_display = " & ".join(all_artists)
            else:
                artist_display = all_artists[0] if all_artists else "Unknown"
            
            # Check if playlist already exists (with artist matching)
            existing = await self.check_existing_album_playlist(
                user_id, album, main_artist, deezer_album_id
            )
            
            # Get all tracks for this album (with artist matching)
            tracks = await self.get_album_tracks(
                user_id, album, main_artist, deezer_album_id
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

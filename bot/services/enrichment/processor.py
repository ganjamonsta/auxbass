"""
TG Player - Enrichment Processor

Orchestrates metadata enrichment from multiple sources.
"""
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from .deezer import deezer_client
from .lastfm import lastfm_client
from .tracklist_matcher import album_tracklist_matcher
from shared.matching import normalize_genre, GENRE_MAPPINGS

logger = logging.getLogger(__name__)


@dataclass
class EnrichmentResult:
    """Result of track enrichment"""
    success: bool
    confidence: int  # 0-100
    
    # Enriched metadata
    album_name: Optional[str] = None
    genre: Optional[str] = None  # Deezer genre (broad category)
    tags: List[str] = field(default_factory=list)  # Last.fm tags (detailed)
    cover_url: Optional[str] = None
    release_date: Optional[str] = None
    track_number: Optional[int] = None
    
    # External IDs
    deezer_track_id: Optional[int] = None
    deezer_album_id: Optional[int] = None
    lastfm_url: Optional[str] = None
    
    # Source info
    source: str = "none"  # deezer, lastfm, combined


class EnrichmentProcessor:
    """
    Processes track enrichment using multiple APIs.
    
    Strategy:
    1. Try Last.fm first (richer database, better for albums/genres)
    2. Enhance with Deezer (covers, track numbers, deezer IDs)
    3. Fallback to tracklist matching if album still not found
    """
    
    async def enrich_track(
        self,
        title: str,
        artist: str,
    ) -> EnrichmentResult:
        """
        Enrich a track with metadata from external APIs.
        
        Args:
            title: Track title
            artist: Artist name
        
        Returns:
            EnrichmentResult with all found metadata
        """
        if not title:
            return EnrichmentResult(success=False, confidence=0)
        
        # Skip placeholder titles - no point searching for "Без названия"
        if title == "Без названия" or title.lower() in ["untitled", "unknown", "без названия"]:
            return EnrichmentResult(success=False, confidence=0)
        
        result = EnrichmentResult(success=False, confidence=0, source="none")
        
        # 1. Try Last.fm first (richer database, priority source)
        if lastfm_client.is_configured:
            lastfm_data = await self._enrich_from_lastfm(title, artist)
            
            if lastfm_data:
                result.success = True
                result.source = "lastfm"
                result.confidence = 70
                
                if lastfm_data.get("album"):
                    result.album_name = lastfm_data["album"]
                
                if lastfm_data.get("genre"):
                    result.genre = lastfm_data["genre"]
                
                if lastfm_data.get("tags"):
                    result.tags = lastfm_data["tags"]
                
                if lastfm_data.get("lastfm_url"):
                    result.lastfm_url = lastfm_data["lastfm_url"]
        
        # 2. Enhance with Deezer (covers, track numbers, IDs)
        deezer_data = await self._enrich_from_deezer(title, artist)
        
        if deezer_data:
            if not result.success:
                result.success = True
                result.source = "deezer"
                result.confidence = 60
            else:
                result.source = "lastfm+deezer"
                result.confidence = min(100, result.confidence + 20)
            
            # Deezer provides covers and track numbers
            if deezer_data.get("cover_url"):
                result.cover_url = deezer_data["cover_url"]
            
            if deezer_data.get("track_number"):
                result.track_number = deezer_data["track_number"]
            
            # Use Deezer album only if Last.fm didn't find one
            if not result.album_name and deezer_data.get("album"):
                result.album_name = deezer_data["album"]
            
            # Always take Deezer IDs
            result.deezer_track_id = deezer_data.get("deezer_track_id")
            result.deezer_album_id = deezer_data.get("deezer_album_id")
            
            if deezer_data.get("release_date"):
                result.release_date = deezer_data["release_date"]
        
        # 3. FALLBACK: If still no album found, try tracklist matching
        # Searches through artist album tracklists (from Last.fm) to find the track
        if not result.album_name and artist and lastfm_client.is_configured:
            tracklist_match = await self._enrich_from_tracklist(title, artist)
            
            if tracklist_match:
                result.success = True
                result.album_name = tracklist_match.get("album_name")
                result.track_number = tracklist_match.get("track_number")
                
                if tracklist_match.get("cover_url") and not result.cover_url:
                    result.cover_url = tracklist_match["cover_url"]
                
                if result.source == "none":
                    result.source = "tracklist"
                else:
                    result.source = f"{result.source}+tracklist"
                
                result.confidence = max(result.confidence, 60)
                logger.info(
                    f"Found album via tracklist: {title} -> {result.album_name} "
                    f"(track #{result.track_number})"
                )
        
        # Normalize genre
        if result.genre:
            result.genre = normalize_genre(result.genre)
        
        return result
    
    async def _enrich_from_deezer(
        self,
        title: str,
        artist: str,
    ) -> Optional[Dict[str, Any]]:
        """Get enrichment data from Deezer"""
        try:
            track = await deezer_client.search_track(title, artist)
            
            if not track:
                return None
            
            result = {
                "deezer_track_id": track.get("id"),
                "confidence": 70,
            }
            
            # Get album info
            album = track.get("album", {})
            if album:
                result["album"] = album.get("title")
                result["deezer_album_id"] = album.get("id")
                
                # Get high-res cover
                cover = album.get("cover_xl") or album.get("cover_big") or album.get("cover_medium")
                if cover:
                    result["cover_url"] = cover
            
            # Get track position in album
            if album.get("id"):
                album_tracks = await deezer_client.get_album_tracks(album["id"])
                for i, t in enumerate(album_tracks, 1):
                    if t.get("id") == track.get("id"):
                        result["track_number"] = i
                        break
                
                # Get release date from album
                full_album = await deezer_client.get_album(album["id"])
                if full_album and full_album.get("release_date"):
                    result["release_date"] = full_album["release_date"]
            
            return result
            
        except Exception as e:
            logger.error(f"Deezer enrichment error: {e}")
            return None
    
    async def _enrich_from_lastfm(
        self,
        title: str,
        artist: str,
    ) -> Optional[Dict[str, Any]]:
        """Get enrichment data from Last.fm including combined tags"""
        try:
            track_info = await lastfm_client.get_track_info(title, artist)
            
            if not track_info:
                # Even without track info, try to get tags
                tags = await lastfm_client.get_combined_tags(title, artist)
                if tags:
                    return {"tags": tags}
                return None
            
            result = {
                "lastfm_url": track_info.get("url"),
            }
            
            # Album
            if track_info.get("album"):
                result["album"] = track_info["album"]
            
            # Get combined tags (track + artist)
            tags = await lastfm_client.get_combined_tags(title, artist)
            if tags:
                result["tags"] = tags
                
                # Also set genre from first tag that maps to a known genre
                for tag in tags:
                    tag_lower = tag.lower()
                    if tag_lower in GENRE_MAPPINGS:
                        result["genre"] = GENRE_MAPPINGS[tag_lower]
                        break
                
                # If no mapping found, use first tag as genre fallback
                if "genre" not in result:
                    result["genre"] = tags[0]
            
            return result
            
        except Exception as e:
            logger.error(f"Last.fm enrichment error: {e}")
            return None
    
    async def _enrich_from_tracklist(
        self,
        title: str,
        artist: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Find album by searching through artist album tracklists.
        Used as fallback when direct track search fails.
        """
        try:
            match = await album_tracklist_matcher.find_album_for_track(
                track_title=title,
                artist=artist,
                match_threshold=0.75
            )
            
            if match:
                return {
                    "album_name": match.get("album_name"),
                    "cover_url": match.get("cover_url"),
                    "track_number": match.get("track_number"),
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Tracklist matching error: {e}")
            return None
    
    async def get_artist_image(self, artist: str) -> Optional[str]:
        """
        Get artist image URL.
        Last.fm is better for artist images than Deezer.
        """
        if not lastfm_client.is_configured:
            return None
        
        try:
            artist_info = await lastfm_client.get_artist_info(artist)
            if artist_info:
                return artist_info.get("image_url")
        except Exception as e:
            logger.error(f"Artist image error: {e}")
        
        return None
    
    async def close(self):
        """Close all API clients"""
        await deezer_client.close()
        await lastfm_client.close()
        await album_tracklist_matcher.close()


# Global instance
enrichment_processor = EnrichmentProcessor()

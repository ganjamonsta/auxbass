"""
TG Player - Enrichment Processor

Orchestrates metadata enrichment from multiple sources.
"""
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from .deezer import deezer_client
from .lastfm import lastfm_client
from shared.matching import normalize_genre, GENRE_MAPPINGS

logger = logging.getLogger(__name__)


@dataclass
class EnrichmentResult:
    """Result of track enrichment"""
    success: bool
    confidence: int  # 0-100
    
    # Enriched metadata
    album_name: Optional[str] = None
    genre: Optional[str] = None
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
    1. Try Deezer first (has album covers, track numbers)
    2. Fall back to Last.fm for genres/tags
    3. Combine results for best coverage
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
        
        result = EnrichmentResult(success=False, confidence=0, source="none")
        
        # Try Deezer first
        deezer_data = await self._enrich_from_deezer(title, artist)
        
        if deezer_data:
            result.success = True
            result.source = "deezer"
            result.confidence = deezer_data.get("confidence", 70)
            result.album_name = deezer_data.get("album")
            result.cover_url = deezer_data.get("cover_url")
            result.track_number = deezer_data.get("track_number")
            result.deezer_track_id = deezer_data.get("deezer_track_id")
            result.deezer_album_id = deezer_data.get("deezer_album_id")
            result.release_date = deezer_data.get("release_date")
        
        # Try Last.fm for additional data (especially genres)
        if lastfm_client.is_configured:
            lastfm_data = await self._enrich_from_lastfm(title, artist)
            
            if lastfm_data:
                if not result.success:
                    result.success = True
                    result.source = "lastfm"
                    result.confidence = 50
                else:
                    result.source = "combined"
                    result.confidence = min(100, result.confidence + 20)
                
                # Use Last.fm album if we don't have one
                if not result.album_name and lastfm_data.get("album"):
                    result.album_name = lastfm_data["album"]
                
                # Last.fm has better genre/tag data
                if lastfm_data.get("genre"):
                    result.genre = lastfm_data["genre"]
                
                if lastfm_data.get("lastfm_url"):
                    result.lastfm_url = lastfm_data["lastfm_url"]
        
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
        """Get enrichment data from Last.fm"""
        try:
            track_info = await lastfm_client.get_track_info(title, artist)
            
            if not track_info:
                return None
            
            result = {
                "lastfm_url": track_info.get("url"),
            }
            
            # Album
            if track_info.get("album"):
                result["album"] = track_info["album"]
            
            # Genre from tags
            tags = track_info.get("tags", [])
            if tags:
                # Find first tag that maps to a known genre
                for tag in tags:
                    tag_lower = tag.lower()
                    if tag_lower in GENRE_MAPPINGS:
                        result["genre"] = GENRE_MAPPINGS[tag_lower]
                        break
                
                # If no mapping found, use first tag
                if "genre" not in result and tags:
                    result["genre"] = tags[0]
            
            return result
            
        except Exception as e:
            logger.error(f"Last.fm enrichment error: {e}")
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


# Global instance
enrichment_processor = EnrichmentProcessor()

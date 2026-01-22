"""
TG Player - Metadata Enrichment Service
Uses MusicBrainz (free, no API key) for metadata lookup
"""
import asyncio
import logging
import re
from typing import Optional, Dict
import aiohttp

logger = logging.getLogger(__name__)

# MusicBrainz API settings
MB_BASE_URL = "https://musicbrainz.org/ws/2"
MB_COVER_URL = "https://coverartarchive.org"
USER_AGENT = "TGPlayer/1.0 (https://github.com/tg-player)"


class MetadataService:
    """Service for fetching additional metadata from external sources"""
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limit_delay = 1.0  # MusicBrainz requires 1 request per second
        self._last_request_time = 0
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"User-Agent": USER_AGENT}
            )
        return self._session
    
    async def _rate_limit(self):
        """Enforce rate limiting for MusicBrainz API"""
        import time
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self._rate_limit_delay:
            await asyncio.sleep(self._rate_limit_delay - elapsed)
        self._last_request_time = time.time()
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _clean_string(self, s: str) -> str:
        """Clean string for search query"""
        # Remove feat., ft., etc.
        s = re.sub(r'\s*[\(\[].*?[\)\]]', '', s)
        s = re.sub(r'\s*(feat\.?|ft\.?|vs\.?)\s+.*', '', s, flags=re.IGNORECASE)
        return s.strip()
    
    async def search_recording(self, title: str, artist: str) -> Optional[Dict]:
        """
        Search MusicBrainz for a recording
        Returns: dict with release_id, artist, title, album, etc.
        """
        if not title and not artist:
            return None
        
        await self._rate_limit()
        session = await self._get_session()
        
        # Build search query
        query_parts = []
        if title:
            clean_title = self._clean_string(title)
            query_parts.append(f'recording:"{clean_title}"')
        if artist:
            clean_artist = self._clean_string(artist)
            query_parts.append(f'artist:"{clean_artist}"')
        
        query = " AND ".join(query_parts)
        
        try:
            url = f"{MB_BASE_URL}/recording"
            params = {
                "query": query,
                "fmt": "json",
                "limit": 1
            }
            
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.warning(f"MusicBrainz search failed: {resp.status}")
                    return None
                
                data = await resp.json()
                recordings = data.get("recordings", [])
                
                if not recordings:
                    return None
                
                rec = recordings[0]
                result = {
                    "mb_recording_id": rec.get("id"),
                    "title": rec.get("title"),
                    "artist": rec.get("artist-credit", [{}])[0].get("name") if rec.get("artist-credit") else None,
                }
                
                # Get release info (album)
                releases = rec.get("releases", [])
                if releases:
                    release = releases[0]
                    result["album"] = release.get("title")
                    result["release_id"] = release.get("id")
                
                return result
                
        except Exception as e:
            logger.error(f"MusicBrainz search error: {e}")
            return None
    
    async def get_cover_art(self, release_id: str) -> Optional[str]:
        """
        Get cover art URL from Cover Art Archive
        Returns: URL to front cover image
        """
        if not release_id:
            return None
        
        await self._rate_limit()
        session = await self._get_session()
        
        try:
            url = f"{MB_COVER_URL}/release/{release_id}"
            
            async with session.get(url, allow_redirects=False) as resp:
                if resp.status == 307:
                    # Has cover art, get front
                    return f"{MB_COVER_URL}/release/{release_id}/front-250"
                elif resp.status == 200:
                    data = await resp.json()
                    images = data.get("images", [])
                    for img in images:
                        if img.get("front"):
                            thumbnails = img.get("thumbnails", {})
                            return thumbnails.get("250") or thumbnails.get("small") or img.get("image")
                    # Return first image if no front
                    if images:
                        return images[0].get("thumbnails", {}).get("250") or images[0].get("image")
                
                return None
                
        except Exception as e:
            logger.error(f"Cover art fetch error: {e}")
            return None
    
    async def enrich_track(self, title: str, artist: str) -> Dict:
        """
        Full enrichment: search recording and get cover art
        Returns: dict with enriched metadata
        """
        result = {
            "enriched": False,
            "title": title,
            "artist": artist,
            "album": None,
            "genre": None,
            "cover_url": None,
        }
        
        # Search for recording
        recording = await self.search_recording(title, artist)
        if not recording:
            return result
        
        result["enriched"] = True
        
        # Update with found data (only if original is empty)
        if not title and recording.get("title"):
            result["title"] = recording["title"]
        if not artist and recording.get("artist"):
            result["artist"] = recording["artist"]
        if recording.get("album"):
            result["album"] = recording["album"]
        
        # Get cover art
        if recording.get("release_id"):
            cover = await self.get_cover_art(recording["release_id"])
            if cover:
                result["cover_url"] = cover
        
        return result


# Global instance
metadata_service = MetadataService()

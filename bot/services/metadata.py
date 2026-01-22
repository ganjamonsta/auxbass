"""
TG Player - Metadata Enrichment Service
Uses Deezer API (free, no API key) for metadata and cover art
"""
import asyncio
import logging
import re
import time
from typing import Optional, Dict
import aiohttp

logger = logging.getLogger(__name__)


class MetadataService:
    """Service for fetching additional metadata from external sources"""
    
    DEEZER_API = "https://api.deezer.com"
    
    USER_AGENT = "TGPlayer/1.0 (https://github.com/ganjamonsta/tg_player)"
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_request_time = 0
        self._rate_limit_delay = 0.25  # Deezer: ~50 req/5sec = 0.1s, we use 0.25 to be safe
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={"User-Agent": self.USER_AGENT}
            )
        return self._session
    
    async def _rate_limit(self):
        """Enforce rate limiting"""
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
        if not s:
            return ""
        # Remove feat., ft., etc.
        s = re.sub(r'\s*[\(\[].*?[\)\]]', '', s)
        s = re.sub(r'\s*(feat\.?|ft\.?|vs\.?)\s+.*', '', s, flags=re.IGNORECASE)
        return s.strip()
    
    async def search_deezer(self, title: str, artist: str) -> Optional[Dict]:
        """
        Search Deezer for track info
        Returns: dict with artist, title, album, genre, cover_url
        """
        if not title and not artist:
            return None
        
        await self._rate_limit()
        session = await self._get_session()
        
        clean_title = self._clean_string(title)
        clean_artist = self._clean_string(artist)
        
        try:
            # Try specific search first
            query = f'track:"{clean_title}" artist:"{clean_artist}"'
            
            async with session.get(
                f"{self.DEEZER_API}/search",
                params={"q": query, "limit": 1}
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"Deezer search failed: {resp.status}")
                    return None
                
                data = await resp.json()
                
                # If no results, try simpler search
                if not data.get("data"):
                    await self._rate_limit()
                    async with session.get(
                        f"{self.DEEZER_API}/search",
                        params={"q": f"{clean_artist} {clean_title}", "limit": 1}
                    ) as resp2:
                        if resp2.status == 200:
                            data = await resp2.json()
                
                if not data.get("data"):
                    return None
                
                track = data["data"][0]
                album = track.get("album", {})
                artist_data = track.get("artist", {})
                
                result = {
                    "title": track.get("title"),
                    "artist": artist_data.get("name"),
                    "album": album.get("title"),
                    "cover_url": album.get("cover_big") or album.get("cover_medium") or album.get("cover"),
                    "deezer_id": track.get("id"),
                    "album_id": album.get("id"),
                }
                
                # Try to get genre from album
                if album.get("id"):
                    genre = await self._get_album_genre(album["id"])
                    if genre:
                        result["genre"] = genre
                
                return result
                
        except asyncio.TimeoutError:
            logger.error("Deezer search timeout")
            return None
        except Exception as e:
            logger.error(f"Deezer search error: {e}")
            return None
    
    async def _get_album_genre(self, album_id: int) -> Optional[str]:
        """Get genre from Deezer album details"""
        await self._rate_limit()
        session = await self._get_session()
        
        try:
            async with session.get(f"{self.DEEZER_API}/album/{album_id}") as resp:
                if resp.status != 200:
                    return None
                
                data = await resp.json()
                genres = data.get("genres", {}).get("data", [])
                
                if genres:
                    return genres[0].get("name")
                return None
                
        except Exception:
            return None
    
    async def enrich_track(self, title: str, artist: str) -> Dict:
        """
        Main method to enrich track metadata
        Returns dict with enriched data and 'enriched' flag
        """
        result = {
            "enriched": False,
            "title": title,
            "artist": artist,
        }
        
        # Try Deezer
        deezer_data = await self.search_deezer(title, artist)
        
        if deezer_data:
            result["enriched"] = True
            result["album"] = deezer_data.get("album")
            result["genre"] = deezer_data.get("genre")
            result["cover_url"] = deezer_data.get("cover_url")
            result["source"] = "deezer"
            logger.info(f"Enriched from Deezer: {title} - {artist}")
        else:
            logger.debug(f"No Deezer data for: {title} - {artist}")
        
        return result


# Global instance
metadata_service = MetadataService()

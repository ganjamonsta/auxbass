"""
TG Player - Metadata Enrichment Service
Uses Deezer API (free, no API key) for metadata and cover art
MusicBrainz as fallback for genres
"""
import asyncio
import logging
import re
import time
from typing import Optional, Dict, List
import aiohttp

logger = logging.getLogger(__name__)


# Common genre mappings from tags
GENRE_KEYWORDS = {
    "rock": "Rock",
    "pop": "Pop", 
    "hip hop": "Hip-Hop",
    "hip-hop": "Hip-Hop",
    "rap": "Hip-Hop",
    "electronic": "Electronic",
    "edm": "Electronic",
    "house": "Electronic",
    "techno": "Electronic",
    "dubstep": "Electronic",
    "dnb": "Drum & Bass",
    "drum and bass": "Drum & Bass",
    "jazz": "Jazz",
    "blues": "Blues",
    "classical": "Classical",
    "metal": "Metal",
    "punk": "Punk",
    "r&b": "R&B",
    "rnb": "R&B",
    "soul": "Soul",
    "country": "Country",
    "folk": "Folk",
    "indie": "Indie",
    "alternative": "Alternative",
    "reggae": "Reggae",
    "latin": "Latin",
    "world": "World",
    "ambient": "Ambient",
    "soundtrack": "Soundtrack",
    "k-pop": "K-Pop",
    "kpop": "K-Pop",
    "j-pop": "J-Pop",
    "jpop": "J-Pop",
    "russian": "Russian",
    "russian rap": "Russian Hip-Hop",
}


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
        Prioritizes album tracks over singles (where album name = track name)
        """
        if not title and not artist:
            return None
        
        await self._rate_limit()
        session = await self._get_session()
        
        clean_title = self._clean_string(title)
        clean_artist = self._clean_string(artist)
        
        try:
            # Try specific search first - get more results to pick best one
            query = f'track:"{clean_title}" artist:"{clean_artist}"'
            
            async with session.get(
                f"{self.DEEZER_API}/search",
                params={"q": query, "limit": 10}  # Get more results to pick best
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
                        params={"q": f"{clean_artist} {clean_title}", "limit": 10}
                    ) as resp2:
                        if resp2.status == 200:
                            data = await resp2.json()
                
                if not data.get("data"):
                    return None
                
                # Pick best result: prefer album tracks over singles
                # Singles usually have album.title == track.title
                tracks = data["data"]
                best_track = None
                
                for track in tracks:
                    album = track.get("album", {})
                    album_title = album.get("title", "")
                    track_title = track.get("title", "")
                    
                    # Skip if album name matches track name (likely a single)
                    if album_title.lower().strip() == track_title.lower().strip():
                        if best_track is None:
                            best_track = track  # Keep as fallback
                        continue
                    
                    # This is likely an album track - use it
                    best_track = track
                    break
                
                if best_track is None:
                    best_track = tracks[0]  # Fall back to first result
                
                track = best_track
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
    
    async def get_album_release_date(self, album_id: int) -> Optional[str]:
        """Get release date from Deezer album details (format: YYYY-MM-DD)"""
        await self._rate_limit()
        session = await self._get_session()
        
        try:
            async with session.get(f"{self.DEEZER_API}/album/{album_id}") as resp:
                if resp.status != 200:
                    return None
                
                data = await resp.json()
                release_date = data.get("release_date")
                
                if release_date:
                    return release_date  # Already in YYYY-MM-DD format
                return None
                
        except Exception as e:
            logger.debug(f"Failed to get album release date: {e}")
            return None
    
    async def search_deezer_album(self, album_name: str, artist: str = "") -> Optional[Dict]:
        """
        Search Deezer for album info by name and artist.
        Returns: dict with album_id, release_date, cover_url
        """
        if not album_name:
            return None
        
        await self._rate_limit()
        session = await self._get_session()
        
        clean_album = self._clean_string(album_name)
        clean_artist = self._clean_string(artist) if artist else ""
        
        try:
            # Search for album
            query = f'album:"{clean_album}"'
            if clean_artist:
                query += f' artist:"{clean_artist}"'
            
            async with session.get(
                f"{self.DEEZER_API}/search/album",
                params={"q": query, "limit": 5}
            ) as resp:
                if resp.status != 200:
                    return None
                
                data = await resp.json()
                
                if not data.get("data"):
                    # Try simpler search
                    await self._rate_limit()
                    simple_query = f"{clean_artist} {clean_album}".strip()
                    async with session.get(
                        f"{self.DEEZER_API}/search/album",
                        params={"q": simple_query, "limit": 5}
                    ) as resp2:
                        if resp2.status == 200:
                            data = await resp2.json()
                
                if not data.get("data"):
                    return None
                
                # Find best match
                albums = data["data"]
                best_album = None
                
                for album in albums:
                    album_title = album.get("title", "").lower().strip()
                    if album_title == clean_album.lower().strip():
                        best_album = album
                        break
                
                if not best_album:
                    best_album = albums[0]
                
                album_id = best_album.get("id")
                
                # Get release date from album details
                release_date = None
                if album_id:
                    release_date = await self.get_album_release_date(album_id)
                
                return {
                    "album_id": album_id,
                    "release_date": release_date,
                    "cover_url": best_album.get("cover_big") or best_album.get("cover_medium"),
                    "title": best_album.get("title"),
                }
                
        except asyncio.TimeoutError:
            logger.error("Deezer album search timeout")
            return None
        except Exception as e:
            logger.error(f"Deezer album search error: {e}")
            return None
    
    def _guess_genre_from_text(self, title: str, artist: str) -> Optional[str]:
        """Try to guess genre from title/artist keywords"""
        text = f"{title} {artist}".lower()
        
        for keyword, genre in GENRE_KEYWORDS.items():
            if keyword in text:
                return genre
        
        return None
    
    async def _search_lastfm_genre(self, artist: str) -> Optional[str]:
        """Get genre from Last.fm artist tags (no API key needed for basic info)"""
        if not artist:
            return None
            
        await self._rate_limit()
        session = await self._get_session()
        
        try:
            # Use Last.fm's public artist info endpoint
            url = f"https://www.last.fm/music/{artist.replace(' ', '+')}"
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                
                text = await resp.text()
                
                # Extract genre tags from page
                import re
                tags = re.findall(r'class="tag"[^>]*>([^<]+)</a>', text)
                
                if tags:
                    # Map to our standard genres
                    for tag in tags[:3]:
                        tag_lower = tag.lower().strip()
                        if tag_lower in GENRE_KEYWORDS:
                            return GENRE_KEYWORDS[tag_lower]
                        # Return first meaningful tag
                        if len(tag) > 2 and tag not in ['seen', 'live']:
                            return tag.title()
                
                return None
                
        except Exception as e:
            logger.debug(f"Last.fm lookup failed: {e}")
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
        
        # Try Deezer first
        deezer_data = await self.search_deezer(title, artist)
        
        if deezer_data:
            result["enriched"] = True
            result["album"] = deezer_data.get("album")
            result["genre"] = deezer_data.get("genre")
            result["cover_url"] = deezer_data.get("cover_url")
            result["source"] = "deezer"
            logger.info(f"Enriched from Deezer: {title} - {artist}")
        
        # If no genre from Deezer, try fallbacks
        if not result.get("genre"):
            # Try keyword-based guess
            guessed = self._guess_genre_from_text(title, artist)
            if guessed:
                result["genre"] = guessed
                result["enriched"] = True
                logger.info(f"Genre guessed from keywords: {guessed}")
            else:
                # Try Last.fm as last resort
                lastfm_genre = await self._search_lastfm_genre(artist)
                if lastfm_genre:
                    result["genre"] = lastfm_genre
                    result["enriched"] = True
                    logger.info(f"Genre from Last.fm: {lastfm_genre}")
        
        if not result["enriched"]:
            logger.debug(f"No enrichment data for: {title} - {artist}")
        
        return result


# Global instance
metadata_service = MetadataService()

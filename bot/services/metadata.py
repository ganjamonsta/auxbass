"""
TG Player - Metadata Enrichment Service
Uses Deezer API (free, no API key) for metadata and cover art
MusicBrainz as fallback for genres
"""
import asyncio
import logging
import re
import time
import unicodedata
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
        """
        Clean string for search query.
        Handles common patterns in user-uploaded tracks:
        - "Track Name prod. Producer" -> "Track Name"
        - "Track (feat. Artist)" -> "Track"
        - "Backstr€€t Boys" -> "Backstreet Boys"
        - "guardianAngels((NO2))" -> "guardian Angels"
        """
        if not s:
            return ""
        
        # Normalize unicode and common character substitutions
        s = unicodedata.normalize('NFKD', s)
        s = s.replace('€', 'e').replace('$', 's').replace('@', 'a')
        s = s.replace(''', "'").replace(''', "'").replace('`', "'")
        
        # Add spaces before capital letters in camelCase (guardianAngels -> guardian Angels)
        s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
        
        # Remove content in parentheses/brackets (including nested)
        # Do multiple passes to handle ((nested)) brackets
        for _ in range(3):
            s = re.sub(r'\s*[\(\[][^\(\)\[\]]*[\)\]]', '', s)
        
        # Remove "prod.", "produced by", etc. and everything after
        s = re.sub(r'\s*(prod\.?|produced\s+by)\s+.*$', '', s, flags=re.IGNORECASE)
        
        # Remove "feat.", "ft.", "featuring", "vs." and everything after
        s = re.sub(r'\s*(feat\.?|ft\.?|featuring|vs\.?)\s+.*$', '', s, flags=re.IGNORECASE)
        
        # Remove trailing special characters
        s = re.sub(r'[\s\-_\.,;:]+$', '', s)
        
        return s.strip()
    
    def _normalize_artist(self, artist: str) -> str:
        """Normalize artist name for comparison"""
        if not artist:
            return ""
        # Clean and lowercase
        artist = self._clean_string(artist).lower()
        # Remove common separators and take first artist
        artist = re.split(r'\s*[,&+]\s*|\s+(?:x|and|with)\s+', artist, flags=re.IGNORECASE)[0]
        # Replace $ with s (for A$AP -> ASAP), then remove other special characters
        artist = artist.replace('$', 's')
        artist = re.sub(r'[^\w\s]', '', artist)
        # Remove extra whitespace
        artist = ' '.join(artist.split())
        return artist.strip()
    
    def _artist_matches(self, source_artist: str, deezer_artist: str, threshold: float = 0.6) -> bool:
        """Check if two artist names match (fuzzy comparison)"""
        norm_source = self._normalize_artist(source_artist)
        norm_deezer = self._normalize_artist(deezer_artist)
        
        if not norm_source or not norm_deezer:
            return False
        
        # Exact match
        if norm_source == norm_deezer:
            return True
        
        # One contains the other
        if norm_source in norm_deezer or norm_deezer in norm_source:
            return True
        
        # Word-based comparison (Jaccard similarity)
        words_source = set(norm_source.split())
        words_deezer = set(norm_deezer.split())
        
        if not words_source or not words_deezer:
            return False
        
        intersection = len(words_source & words_deezer)
        union = len(words_source | words_deezer)
        
        return (intersection / union) >= threshold
    
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
                
                # Pick best result: 
                # 1. Must match artist
                # 2. Prefer album tracks over singles (where album name = track name)
                tracks = data["data"]
                best_track = None
                best_track_is_single = True
                
                for track in tracks:
                    album = track.get("album", {})
                    album_title = album.get("title", "")
                    track_title = track.get("title", "")
                    deezer_artist = track.get("artist", {}).get("name", "")
                    
                    # Check if artist matches
                    if not self._artist_matches(artist, deezer_artist):
                        continue  # Skip tracks from different artists
                    
                    # Check if this is a single (album name = track name)
                    is_single = album_title.lower().strip() == track_title.lower().strip()
                    
                    if is_single:
                        # Keep as fallback if no better option
                        if best_track is None:
                            best_track = track
                            best_track_is_single = True
                        continue
                    
                    # This is an album track with matching artist - use it!
                    best_track = track
                    best_track_is_single = False
                    break
                
                # If no matching artist found, DO NOT use random results!
                # This was causing wrong album assignments (e.g., Bladee "Flatline" -> blanke "FLATLINE")
                if best_track is None:
                    logger.debug(f"No artist match for '{artist}' in Deezer results, skipping enrichment")
                    return None
                
                track = best_track
                album = track.get("album", {})
                artist_data = track.get("artist", {})
                
                # Additional validation: skip if album name equals track name (likely a single or misattribution)
                album_title = album.get("title", "")
                track_title = track.get("title", "")
                if album_title.lower().strip() == track_title.lower().strip():
                    logger.debug(f"Skipping single-like result: album '{album_title}' = track '{track_title}'")
                    # Still return cover and genre, but not the album name
                    album = {}  # Clear album to prevent wrong album assignment
                
                # Build result - only include album if it's valid and different from track title
                album_name = album.get("title")
                if album_name and album_name.lower().strip() == track.get("title", "").lower().strip():
                    album_name = None  # Don't use single-like albums
                    
                result = {
                    "title": track.get("title"),
                    "artist": artist_data.get("name"),
                    "album": album_name,
                    "cover_url": album.get("cover_big") or album.get("cover_medium") or album.get("cover"),
                    "deezer_id": track.get("id"),
                    "album_id": album.get("id") if album_name else None,  # No album_id if no valid album
                }
                
                # Try to get genre and release_date from album
                if album.get("id"):
                    genre = await self._get_album_genre(album["id"])
                    if genre:
                        result["genre"] = genre
                    
                    # Get release date
                    release_date = await self.get_album_release_date(album["id"])
                    if release_date:
                        result["release_date"] = release_date
                
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
                
                # Find best match - must match artist if provided
                albums = data["data"]
                best_album = None
                
                for album in albums:
                    album_title = album.get("title", "").lower().strip()
                    album_artist = album.get("artist", {}).get("name", "")
                    
                    # Check artist match if we have one
                    if clean_artist and not self._artist_matches(artist, album_artist):
                        continue  # Skip albums from different artists
                    
                    # Check title match
                    if album_title == clean_album.lower().strip():
                        best_album = album
                        break
                    
                    # Keep first artist-matching album as fallback
                    if best_album is None:
                        best_album = album
                
                # If no artist match found but we have results, use first as last resort
                if not best_album and albums:
                    logger.debug(f"No artist match for album '{album_name}' by '{artist}', using first result")
                    best_album = albums[0]
                
                if not best_album:
                    return None
                
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
    
    async def _get_lastfm_album_release_date(
        self, artist: str, album: str, api_key: str, session
    ) -> Optional[str]:
        """
        Get album release date from Last.fm album.getInfo API.
        Returns date in YYYY-MM-DD format or None.
        """
        await self._rate_limit()
        
        try:
            params = {
                "method": "album.getInfo",
                "api_key": api_key,
                "artist": artist,
                "album": album,
                "format": "json"
            }
            
            async with session.get(
                "https://ws.audioscrobbler.com/2.0/",
                params=params
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
            
            if "error" in data:
                return None
            
            album_data = data.get("album", {})
            # Last.fm returns "releasedate" like "6 Apr 1999, 00:00"
            # NOTE: Do NOT use wiki.published - it's when the wiki was edited, not the release date!
            release_date_str = album_data.get("releasedate", "").strip()
            
            if not release_date_str:
                return None
            
            # Parse date - formats: "6 Apr 1999, 00:00" or "06 Apr 2020, 18:00"
            try:
                from datetime import datetime
                # Remove time part if present
                date_part = release_date_str.split(",")[0].strip()
                
                # Try parsing "6 Apr 1999" format
                for fmt in ["%d %b %Y", "%d %B %Y", "%Y-%m-%d", "%Y"]:
                    try:
                        dt = datetime.strptime(date_part, fmt)
                        return dt.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
                
                # If just a year
                if date_part.isdigit() and len(date_part) == 4:
                    return f"{date_part}-01-01"
                    
                return None
            except Exception:
                return None
                
        except Exception as e:
            logger.debug(f"Last.fm album.getInfo failed: {e}")
            return None

    async def search_lastfm_track(self, title: str, artist: str) -> Optional[Dict]:
        """
        Search Last.fm for track info as fallback when Deezer fails.
        Returns: dict with artist, title, album, cover_url
        """
        from shared.config import get_settings
        settings = get_settings()
        
        if not settings.lastfm_api_key:
            return None
        
        await self._rate_limit()
        session = await self._get_session()
        
        clean_title = self._clean_string(title)
        clean_artist = self._clean_string(artist)
        
        try:
            params = {
                "method": "track.getInfo",
                "api_key": settings.lastfm_api_key,
                "artist": clean_artist,
                "track": clean_title,
                "format": "json"
            }
            
            async with session.get(
                "https://ws.audioscrobbler.com/2.0/",
                params=params
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
            
            if "error" in data:
                # Try search instead of exact match
                await self._rate_limit()
                params = {
                    "method": "track.search",
                    "api_key": settings.lastfm_api_key,
                    "track": clean_title,
                    "artist": clean_artist,
                    "format": "json",
                    "limit": 5
                }
                
                async with session.get(
                    "https://ws.audioscrobbler.com/2.0/",
                    params=params
                ) as resp2:
                    if resp2.status != 200:
                        return None
                    search_data = await resp2.json()
                
                results = search_data.get("results", {}).get("trackmatches", {}).get("track", [])
                if not results:
                    return None
                
                # Find matching artist
                for r in results:
                    if self._artist_matches(artist, r.get("artist", "")):
                        # Get full track info
                        await self._rate_limit()
                        params = {
                            "method": "track.getInfo",
                            "api_key": settings.lastfm_api_key,
                            "artist": r.get("artist"),
                            "track": r.get("name"),
                            "format": "json"
                        }
                        async with session.get(
                            "https://ws.audioscrobbler.com/2.0/",
                            params=params
                        ) as resp3:
                            if resp3.status == 200:
                                data = await resp3.json()
                                if "error" not in data:
                                    break
                else:
                    return None
            
            track_data = data.get("track", {})
            if not track_data:
                return None
            
            album = track_data.get("album", {})
            album_title = album.get("title") if album else None
            album_artist = album.get("artist") if album else None
            
            # Get largest album image
            cover_url = None
            if album and album.get("image"):
                images = album.get("image", [])
                for img in reversed(images):  # Largest last
                    if img.get("#text"):
                        cover_url = img.get("#text")
                        break
            
            # Get tags for genre
            genre = None
            tags = track_data.get("toptags", {}).get("tag", [])
            if tags:
                for tag in tags[:3]:
                    tag_name = tag.get("name", "").lower()
                    if tag_name in GENRE_KEYWORDS:
                        genre = GENRE_KEYWORDS[tag_name]
                        break
                    elif len(tag_name) > 2:
                        genre = tag.get("name", "").title()
                        break
            
            # Get release date from album.getInfo
            release_date = None
            if album_title and album_artist:
                release_date = await self._get_lastfm_album_release_date(
                    album_artist, album_title, settings.lastfm_api_key, session
                )
            
            return {
                "title": track_data.get("name"),
                "artist": track_data.get("artist", {}).get("name"),
                "album": album_title,
                "cover_url": cover_url,
                "genre": genre,
                "release_date": release_date,
                "source": "lastfm",
            }
            
        except Exception as e:
            logger.debug(f"Last.fm track search failed: {e}")
            return None
    
    async def enrich_track(self, title: str, artist: str) -> Dict:
        """
        Main method to enrich track metadata.
        Uses Deezer as primary source, Last.fm as fallback.
        Returns dict with enriched data and 'enriched' flag.
        """
        result = {
            "enriched": False,
            "title": title,
            "artist": artist,
        }
        
        # Try Deezer first (has album_id for grouping)
        deezer_data = await self.search_deezer(title, artist)
        
        if deezer_data:
            result["enriched"] = True
            result["album"] = deezer_data.get("album")
            result["genre"] = deezer_data.get("genre")
            result["cover_url"] = deezer_data.get("cover_url")
            result["album_id"] = deezer_data.get("album_id")
            result["deezer_id"] = deezer_data.get("deezer_id")
            result["source"] = "deezer"
            logger.info(f"Enriched from Deezer: {title} - {artist} -> album: {deezer_data.get('album')}")
        else:
            # Deezer failed - try Last.fm as fallback
            lastfm_data = await self.search_lastfm_track(title, artist)
            
            if lastfm_data:
                result["enriched"] = True
                result["album"] = lastfm_data.get("album")
                result["genre"] = lastfm_data.get("genre")
                result["cover_url"] = lastfm_data.get("cover_url")
                result["release_date"] = lastfm_data.get("release_date")
                # No album_id from Last.fm - will group by album name
                result["source"] = "lastfm"
                logger.info(f"Enriched from Last.fm: {title} - {artist} -> album: {lastfm_data.get('album')}, date: {lastfm_data.get('release_date')}")
        
        # If still no genre, try fallbacks
        if not result.get("genre"):
            # Try keyword-based guess
            guessed = self._guess_genre_from_text(title, artist)
            if guessed:
                result["genre"] = guessed
                result["enriched"] = True
                logger.debug(f"Genre guessed from keywords: {guessed}")
            else:
                # Try Last.fm artist tags
                lastfm_genre = await self._search_lastfm_genre(artist)
                if lastfm_genre:
                    result["genre"] = lastfm_genre
                    result["enriched"] = True
                    logger.debug(f"Genre from Last.fm artist: {lastfm_genre}")
        
        if not result["enriched"]:
            logger.debug(f"No enrichment data for: {title} - {artist}")
        
        return result


# Global instance
metadata_service = MetadataService()

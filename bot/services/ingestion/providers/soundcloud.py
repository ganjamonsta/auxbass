"""
TG Player - SoundCloud Provider
Extracts metadata and audio from SoundCloud tracks, playlists, and sets using yt-dlp.
"""
import os
import re
import asyncio
import logging
import aiohttp
import time
from typing import Optional, List, Dict, Any, Tuple

import yt_dlp

from ..base import BaseMusicProvider, SourceEntity, TrackMetadata, DownloadedAudio, EntityType

logger = logging.getLogger(__name__)

SC_URL_PATTERN = re.compile(
    r"^https?://(?:(?:m|www)\.)?(?:soundcloud\.com|on\.soundcloud\.com)/[\w\-_./]+",
    re.IGNORECASE
)


def _improve_sc_thumbnail(thumb_url: Optional[str]) -> Optional[str]:
    """Upgrade SoundCloud thumbnail to 500x500 resolution."""
    if not thumb_url:
        return None
    for pattern in ("-large.", "-small.", "-badge.", "-t67x67.", "-t300x300.", "-crop."):
        if pattern in thumb_url:
            return thumb_url.replace(pattern, "-t500x500.")
    return thumb_url


def _extract_sc_thumbnail(entry: Optional[dict], fallback: Optional[str] = None) -> Optional[str]:
    """Extract best available thumbnail from a SoundCloud entry dictionary."""
    if not entry or not isinstance(entry, dict):
        return _improve_sc_thumbnail(fallback)

    # 1. Check thumbnails list (populated in extract_flat mode)
    thumbnails = entry.get("thumbnails")
    if isinstance(thumbnails, list) and thumbnails:
        # High quality targets
        for target_id in ("t500x500", "original", "t300x300", "crop", "large"):
            for t in thumbnails:
                if isinstance(t, dict) and t.get("id") == target_id and t.get("url"):
                    return _improve_sc_thumbnail(t["url"])

        # Fallback to the last one (usually highest quality)
        for t in reversed(thumbnails):
            if isinstance(t, dict) and t.get("url"):
                return _improve_sc_thumbnail(t["url"])

    # 2. Check direct fields
    direct = entry.get("thumbnail") or entry.get("artwork_url") or entry.get("avatar_url") or fallback
    return _improve_sc_thumbnail(direct)


def _parse_artist_and_title(raw_title: str, uploader: Optional[str]) -> tuple[str, str]:
    """
    SoundCloud titles often follow 'Artist - Title' format.
    Extract clean artist and title.
    """
    clean_title = raw_title.strip()
    artist = (uploader or "SoundCloud").strip()

    if " - " in clean_title:
        parts = clean_title.split(" - ", 1)
        part_artist = parts[0].strip()
        part_title = parts[1].strip()
        if part_artist and part_title:
            return part_artist, part_title

    return artist, clean_title


class SoundCloudProvider(BaseMusicProvider):
    """SoundCloud music provider powered by yt-dlp."""
    name: str = "soundcloud"

    def can_handle(self, url: str) -> bool:
        return bool(SC_URL_PATTERN.match(url.strip()))

    async def resolve_entity(self, url: str) -> SourceEntity:
        """Inspect SoundCloud URL to determine if it's a single track or playlist/set."""
        clean_url = url.strip()

        def _extract():
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": "in_playlist",
                "skip_download": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(clean_url, download=False)

        try:
            info = await asyncio.to_thread(_extract)
        except Exception as e:
            err_str = str(e).lower()
            if "drm protected" in err_str or "proxy" in err_str or "unable to download" in err_str:
                logger.info(f"[SoundCloud] yt-dlp inspection failed for '{clean_url}', attempting oEmbed fallback: {e}")
                try:
                    info = await self._resolve_drm_via_oembed(clean_url)
                except Exception as oe_err:
                    logger.warning(f"[SoundCloud] oEmbed fallback failed: {oe_err}")
                    raise e from None
            else:
                raise

        if not info:
            raise ValueError(f"Could not resolve SoundCloud URL: {clean_url}")

        is_playlist = (
            info.get("_type") == "playlist"
            or "entries" in info
            or "/sets/" in clean_url
        )

        if is_playlist:
            raw_entries = info.get("entries") or []
            entries = list(raw_entries)
            title = info.get("title") or "SoundCloud Playlist"
            author = info.get("uploader") or info.get("channel") or "SoundCloud"
            cover = _extract_sc_thumbnail(info, info.get("thumbnail"))
            return SourceEntity(
                provider_name=self.name,
                entity_type=EntityType.PLAYLIST,
                url=clean_url,
                title=title,
                author=author,
                cover_url=cover,
                track_count=len(entries),
                raw_data=info,
            )
        else:
            raw_title = info.get("title") or "SoundCloud Track"
            uploader = info.get("uploader") or info.get("artist")
            artist, title = _parse_artist_and_title(raw_title, uploader)
            cover = _extract_sc_thumbnail(info, info.get("thumbnail"))
            return SourceEntity(
                provider_name=self.name,
                entity_type=EntityType.TRACK,
                url=clean_url,
                title=title,
                author=artist,
                cover_url=cover,
                track_count=1,
                raw_data=info,
            )

    async def _resolve_drm_via_oembed(self, url: str) -> dict:
        """Fetch basic track metadata from SoundCloud oEmbed API for DRM tracks."""
        import aiohttp
        oembed_url = f"https://soundcloud.com/oembed?format=json&url={url}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(oembed_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    raise ValueError(f"SoundCloud oEmbed failed (HTTP {resp.status})")
                data = await resp.json()

        author = data.get("author_name") or "SoundCloud"
        raw_title = data.get("title") or "Track"
        # Often formatted as: "Track Title by author"
        if raw_title.lower().endswith(f" by {author.lower()}"):
            raw_title = raw_title[: -(len(author) + 4)].strip()

        # Extract track id from iframe html if possible
        html = data.get("html") or ""
        m = re.search(r"/tracks%2F(\d+)", html) or re.search(r"/tracks/(\d+)", html)
        ext_id = m.group(1) if m else None

        return {
            "_type": "url",
            "title": raw_title,
            "uploader": author,
            "artist": author,
            "thumbnail": data.get("thumbnail_url"),
            "id": ext_id,
            "is_drm": True,
        }

    async def fetch_tracklist(self, entity: SourceEntity) -> List[TrackMetadata]:
        """Fetch all track metadata from the entity."""
        if entity.entity_type == EntityType.TRACK:
            raw = entity.raw_data or {}
            raw_title = raw.get("title") or entity.title
            uploader = raw.get("uploader") or entity.author
            artist, title = _parse_artist_and_title(raw_title, uploader)
            duration = int(raw.get("duration") or 0) or None
            cover = _extract_sc_thumbnail(raw, entity.cover_url)

            return [
                TrackMetadata(
                    provider_name=self.name,
                    url=entity.url,
                    title=title,
                    artist=artist,
                    duration=duration,
                    cover_url=cover,
                    external_id=str(raw.get("id") or ""),
                    extra={"uploader": uploader},
                )
            ]

        # Playlist / Set
        raw = entity.raw_data or {}
        entries = raw.get("entries")

        # If flat entries don't have full info, or if entries are missing, re-extract
        if not entries:
            def _extract_full():
                ydl_opts = {
                    "quiet": True,
                    "no_warnings": True,
                    "extract_flat": True,
                    "skip_download": True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(entity.url, download=False)

            info = await asyncio.to_thread(_extract_full)
            entries = info.get("entries") or []

        tracks: List[TrackMetadata] = []
        for idx, entry in enumerate(entries, start=1):
            if not isinstance(entry, dict):
                continue

            raw_title = entry.get("title") or f"Track {idx}"
            uploader = entry.get("uploader") or entity.author
            artist, title = _parse_artist_and_title(raw_title, uploader)
            track_url = entry.get("webpage_url") or entry.get("url") or ""
            if track_url and not track_url.startswith("http"):
                track_url = f"https://soundcloud.com/{track_url.lstrip('/')}"
            if not track_url:
                track_url = f"{entity.url}#{idx}"
            duration = int(entry.get("duration") or 0) or None
            cover = _extract_sc_thumbnail(entry, entity.cover_url)

            tracks.append(
                TrackMetadata(
                    provider_name=self.name,
                    url=track_url,
                    title=title,
                    artist=artist,
                    album=entity.title,
                    duration=duration,
                    cover_url=cover,
                    track_number=idx,
                    external_id=str(entry.get("id") or ""),
                    extra={"uploader": uploader},
                )
            )

        return tracks

    async def download_track(self, track_meta: TrackMetadata, temp_dir: str) -> DownloadedAudio:
        """Download track to MP3 and fetch high quality cover artwork."""
        os.makedirs(temp_dir, exist_ok=True)
        out_template = os.path.join(temp_dir, "audio.%(ext)s")

        def _download():
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": out_template,
                "concurrent_fragment_downloads": 5,
                "color": "never",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "320",
                    }
                ],
                "quiet": True,
                "no_warnings": True,
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([track_meta.url])
            except Exception as e:
                err_msg = str(e)
                if "drm protected" in err_msg.lower():
                    raise ValueError("DRM_PROTECTED") from e
                raise

        try:
            await asyncio.to_thread(_download)
        except Exception as e:
            if "drm protected" in str(e).lower() or "DRM_PROTECTED" in str(e):
                logger.info(
                    f"SoundCloud DRM encountered for '{track_meta.artist} - {track_meta.title}'. "
                    f"Resolving unencrypted alternative stream..."
                )
                from ..audio_resolver import audio_resolver
                try:
                    return await audio_resolver.resolve_and_download(
                        track_meta, temp_dir, exclude_urls={track_meta.url}
                    )
                except Exception as resolve_err:
                    logger.warning(f"AudioResolver fallback failed for '{track_meta.title}': {resolve_err}")
                    raise ValueError("Этот трек защищён DRM (SoundCloud Go+) и недоступен для бесплатного воспроизведения.") from e
            raise

        # Expected output is audio.mp3
        expected_audio = os.path.join(temp_dir, "audio.mp3")
        if not os.path.exists(expected_audio):
            # Fallback: look for any audio file in temp_dir
            for f in os.listdir(temp_dir):
                if f.lower().endswith((".mp3", ".m4a", ".opus", ".ogg")):
                    expected_audio = os.path.join(temp_dir, f)
                    break

        if not os.path.exists(expected_audio):
            raise FileNotFoundError(f"Failed to download audio for track: {track_meta.title}")

        file_size = os.path.getsize(expected_audio)

        # Download thumbnail cover if available
        cover_path = None
        if track_meta.cover_url:
            cover_path = os.path.join(temp_dir, "cover.jpg")
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(track_meta.cover_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            content = await resp.read()
                            with open(cover_path, "wb") as f:
                                f.write(content)
                        else:
                            cover_path = None
            except Exception as e:
                logger.warning(f"Could not download cover for track {track_meta.title}: {e}")
                cover_path = None

        return DownloadedAudio(
            audio_path=expected_audio,
            cover_path=cover_path,
            metadata=track_meta,
            file_size=file_size,
            mime_type="audio/mpeg",
        )

    _search_cache: Dict[str, Tuple[float, List[TrackMetadata]]] = {}
    _SEARCH_CACHE_TTL = 300  # 5 minutes

    async def search(self, query: str, limit: int = 30) -> List[TrackMetadata]:
        """Search SoundCloud for tracks matching query."""
        clean_query = query.strip()
        # SoundCloud scsearch cannot handle hashtags
        if not clean_query or clean_query.startswith("#"):
            return []

        cache_key = clean_query.lower()
        now = time.time()
        if cache_key in self._search_cache:
            ts, cached_results = self._search_cache[cache_key]
            if now - ts < self._SEARCH_CACHE_TTL and len(cached_results) >= limit:
                return cached_results[:limit]

        def _search():
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "skip_download": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(f"scsearch{limit}:{clean_query}", download=False)

        try:
            info = await asyncio.to_thread(_search)
            entries = info.get("entries") or []
        except Exception as e:
            logger.warning(f"SoundCloud search failed for query '{clean_query}': {e}")
            return []

        results: List[TrackMetadata] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            raw_title = entry.get("title") or "SoundCloud Track"
            uploader = entry.get("uploader") or entry.get("channel") or "SoundCloud"
            artist, title = _parse_artist_and_title(raw_title, uploader)
            track_url = entry.get("webpage_url") or entry.get("url") or ""
            if not track_url:
                continue
            duration = int(entry.get("duration") or 0) or None
            cover = _extract_sc_thumbnail(entry)

            results.append(
                TrackMetadata(
                    provider_name=self.name,
                    url=track_url,
                    title=title,
                    artist=artist,
                    duration=duration,
                    cover_url=cover,
                    external_id=str(entry.get("id") or ""),
                    extra={"uploader": uploader},
                )
            )

        self._search_cache[cache_key] = (now, results)
        if len(self._search_cache) > 200:
            for k in list(self._search_cache.keys()):
                if now - self._search_cache[k][0] >= self._SEARCH_CACHE_TTL:
                    self._search_cache.pop(k, None)

        return results

    _cached_client_id: Optional[str] = None

    async def get_client_id(self) -> str:
        """Get or discover a valid SoundCloud API client_id using yt-dlp."""
        if self._cached_client_id:
            return self._cached_client_id

        def _discover():
            ydl_opts = {"quiet": True, "no_warnings": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ie = yt_dlp.extractor.soundcloud.SoundcloudUserIE(ydl)
                ie.initialize()
                return ie._CLIENT_ID

        try:
            cid = await asyncio.to_thread(_discover)
            if cid:
                self._cached_client_id = cid
                return cid
        except Exception as e:
            logger.warning(f"Failed to extract SoundCloud client_id via yt-dlp: {e}")

        # Fallback default client_id
        return "Pb72ranhoyt6gw7hM7TkzUItXlMWSNSo"

    async def resolve_user_profile(self, username_or_url: str, auth_token: Optional[str] = None) -> dict:
        """
        Resolve SoundCloud user profile by username or URL.
        Returns user info dictionary: external_id, username, display_name, avatar_url, profile_url, likes_count, tracks_count.
        """
        raw = username_or_url.strip()
        if "soundcloud.com/" in raw:
            m = re.search(r"soundcloud\.com/([a-zA-Z0-9_\-]+)", raw)
            permalink = m.group(1) if m else raw.rstrip("/").split("/")[-1]
        else:
            permalink = raw.lstrip("@")

        client_id = await self.get_client_id()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }
        if auth_token:
            headers["Authorization"] = f"OAuth {auth_token.strip()}"

        target_url = f"https://soundcloud.com/{permalink}"
        api_url = f"https://api-v2.soundcloud.com/resolve?url={target_url}&client_id={client_id}"

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(api_url) as resp:
                if resp.status == 404:
                    raise ValueError(f"Пользователь SoundCloud '{permalink}' не найден.")
                if resp.status != 200:
                    text = await resp.text()
                    raise ValueError(f"SoundCloud API error ({resp.status}): {text[:100]}")
                data = await resp.json()

        avatar = _improve_sc_thumbnail(data.get("avatar_url"))
        likes_count = data.get("likes_count") or data.get("public_favorites_count") or 0
        tracks_count = data.get("track_count") or 0

        return {
            "external_id": str(data.get("id")),
            "username": data.get("permalink") or permalink,
            "display_name": data.get("username") or permalink,
            "profile_url": data.get("permalink_url") or target_url,
            "avatar_url": avatar,
            "likes_count": likes_count,
            "tracks_count": tracks_count,
        }

    async def fetch_user_likes(
        self,
        external_id_or_username: str,
        limit: int = 50,
        next_href: Optional[str] = None,
        auth_token: Optional[str] = None,
    ) -> tuple[List[TrackMetadata], Optional[str]]:
        """
        Fetch liked tracks for a SoundCloud user.
        Returns (list_of_tracks, next_cursor_href).
        """
        client_id = await self.get_client_id()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }
        if auth_token:
            headers["Authorization"] = f"OAuth {auth_token.strip()}"

        if next_href:
            req_url = next_href
            if "client_id=" not in req_url:
                delim = "&" if "?" in req_url else "?"
                req_url = f"{req_url}{delim}client_id={client_id}"
        else:
            user_id = str(external_id_or_username).strip()
            if not user_id.isdigit():
                profile = await self.resolve_user_profile(user_id, auth_token=auth_token)
                user_id = profile["external_id"]

            req_url = f"https://api-v2.soundcloud.com/users/{user_id}/likes?limit={limit}&client_id={client_id}"

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(req_url) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise ValueError(f"SoundCloud likes error ({resp.status}): {text[:100]}")
                data = await resp.json()

        collection = data.get("collection") or []
        next_url = data.get("next_href")

        tracks: List[TrackMetadata] = []
        for item in collection:
            if not isinstance(item, dict):
                continue
            tr = item.get("track") or item
            if not isinstance(tr, dict) or not tr.get("title"):
                continue

            raw_title = tr.get("title") or "SoundCloud Track"
            user_obj = tr.get("user") or {}
            uploader = user_obj.get("username") or "SoundCloud"
            artist, title = _parse_artist_and_title(raw_title, uploader)

            track_url = tr.get("permalink_url") or ""
            if not track_url and tr.get("permalink"):
                track_url = f"https://soundcloud.com/{user_obj.get('permalink', 'artist')}/{tr.get('permalink')}"
            if not track_url:
                continue

            dur_raw = tr.get("duration") or 0
            duration = int(dur_raw / 1000) if dur_raw > 1000 else int(dur_raw) or None
            cover = _improve_sc_thumbnail(tr.get("artwork_url") or user_obj.get("avatar_url"))

            tracks.append(
                TrackMetadata(
                    provider_name=self.name,
                    url=track_url,
                    title=title,
                    artist=artist,
                    duration=duration,
                    cover_url=cover,
                    external_id=str(tr.get("id") or ""),
                    extra={"uploader": uploader, "liked_at": item.get("created_at")},
                )
            )

        return tracks, next_url


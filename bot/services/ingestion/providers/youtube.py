"""
TG Player - YouTube & YouTube Music Provider
Extracts metadata and audio from YouTube and YouTube Music tracks, albums, and playlists using yt-dlp.
"""
import os
import re
import asyncio
import logging
import aiohttp
from typing import Optional, List, Dict, Any, Tuple, Callable

import yt_dlp

from shared.matching import clean_track_metadata
from ..base import (
    BaseMusicProvider,
    SourceEntity,
    TrackMetadata,
    DownloadedAudio,
    EntityType,
)

logger = logging.getLogger(__name__)

# Matches youtube.com, music.youtube.com, youtu.be
YT_URL_PATTERN = re.compile(
    r"^https?://(?:(?:music|www|m)\.)?(?:youtube\.com|youtu\.be)/(?:watch\?v=|embed/|v/|shorts/|playlist\?list=|channel/|browse/|album/)?[\w\-_./?=&]+",
    re.IGNORECASE,
)


def _improve_yt_thumbnail(thumb_url: Optional[str]) -> Optional[str]:
    """Upgrade YouTube thumbnail to highest resolution available."""
    if not thumb_url:
        return None
    # If standard hqdefault / mqdefault is present, try maxresdefault
    if "hqdefault.jpg" in thumb_url or "mqdefault.jpg" in thumb_url:
        return thumb_url.replace("hqdefault.jpg", "maxresdefault.jpg").replace("mqdefault.jpg", "maxresdefault.jpg")
    return thumb_url


def _extract_yt_thumbnail(entry: Optional[dict], fallback: Optional[str] = None) -> Optional[str]:
    """Extract best available thumbnail from a YouTube entry dictionary."""
    if not entry or not isinstance(entry, dict):
        return _improve_yt_thumbnail(fallback)

    thumbnails = entry.get("thumbnails")
    if isinstance(thumbnails, list) and thumbnails:
        # Pick largest by width / height / preference
        sorted_thumbs = sorted(
            [t for t in thumbnails if isinstance(t, dict) and t.get("url")],
            key=lambda x: (x.get("width") or 0) * (x.get("height") or 0) + (x.get("preference") or 0),
            reverse=True,
        )
        if sorted_thumbs:
            return sorted_thumbs[0]["url"]

    direct = entry.get("thumbnail") or fallback
    return _improve_yt_thumbnail(direct)


def _parse_artist_and_title(
    raw_title: str,
    uploader: Optional[str] = None,
    channel: Optional[str] = None,
    track_field: Optional[str] = None,
    artist_field: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Extract clean artist and title from YouTube video metadata.
    Handles YouTube Music 'Artist - Topic' channels and 'Artist - Title' video titles.
    """
    # 1. If explicit track/artist metadata is present in yt-dlp info (common in YouTube Music)
    if track_field and artist_field:
        clean_t, clean_a = clean_track_metadata(track_field, artist_field)
        return clean_a or artist_field, clean_t or track_field

    raw_clean_title = raw_title.strip()
    raw_artist = (uploader or channel or "YouTube").strip()

    # Strip ' - Topic' suffix from YouTube Music auto-generated channels
    if raw_artist.lower().endswith(" - topic"):
        raw_artist = raw_artist[:-8].strip()

    # 2. Check if title contains 'Artist - Title'
    if " - " in raw_clean_title:
        parts = raw_clean_title.split(" - ", 1)
        part_artist = parts[0].strip()
        part_title = parts[1].strip()
        if part_artist and part_title:
            clean_t, clean_a = clean_track_metadata(part_title, part_artist)
            return clean_a or part_artist, clean_t or part_title

    clean_t, clean_a = clean_track_metadata(raw_clean_title, raw_artist)
    return clean_a or raw_artist, clean_t or raw_clean_title


class YouTubeMusicProvider(BaseMusicProvider):
    """YouTube and YouTube Music audio provider powered by yt-dlp."""

    name: str = "youtube"

    def can_handle(self, url: str) -> bool:
        clean_url = url.strip()
        if not YT_URL_PATTERN.match(clean_url):
            return False
        # Ensure it's a youtube domain
        return any(d in clean_url.lower() for d in ("youtube.com", "youtu.be", "music.youtube.com"))

    async def resolve_entity(self, url: str) -> SourceEntity:
        """Inspect YouTube/YouTube Music URL to determine if it's a single track or playlist/album."""
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

        info = await asyncio.to_thread(_extract)
        if not info:
            raise ValueError(f"Could not resolve YouTube URL: {clean_url}")

        is_playlist = (
            info.get("_type") == "playlist"
            or "entries" in info
            or "list=" in clean_url
        )

        if is_playlist:
            raw_entries = info.get("entries") or []
            entries = list(raw_entries)
            title = info.get("title") or "YouTube Playlist"
            author = info.get("uploader") or info.get("channel") or "YouTube"
            if author.lower().endswith(" - topic"):
                author = author[:-8].strip()
            cover = _extract_yt_thumbnail(info, info.get("thumbnail"))

            entity_type = EntityType.ALBUM if ("album" in clean_url.lower() or "album" in title.lower()) else EntityType.PLAYLIST

            return SourceEntity(
                provider_name=self.name,
                entity_type=entity_type,
                url=clean_url,
                title=title,
                author=author,
                cover_url=cover,
                track_count=len(entries),
                raw_data=info,
            )
        else:
            raw_title = info.get("title") or "YouTube Track"
            uploader = info.get("uploader") or info.get("channel")
            track_field = info.get("track")
            artist_field = info.get("artist")
            artist, title = _parse_artist_and_title(raw_title, uploader, track_field=track_field, artist_field=artist_field)
            cover = _extract_yt_thumbnail(info, info.get("thumbnail"))

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

    async def fetch_tracklist(self, entity: SourceEntity) -> List[TrackMetadata]:
        """Fetch all track metadata from the entity."""
        if entity.entity_type == EntityType.TRACK:
            raw = entity.raw_data or {}
            raw_title = raw.get("title") or entity.title
            uploader = raw.get("uploader") or raw.get("channel") or entity.author
            track_field = raw.get("track")
            artist_field = raw.get("artist")
            artist, title = _parse_artist_and_title(raw_title, uploader, track_field=track_field, artist_field=artist_field)
            duration = int(raw.get("duration") or 0) or None
            cover = _extract_yt_thumbnail(raw, entity.cover_url)

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

        # Playlist / Album
        raw = entity.raw_data or {}
        entries = raw.get("entries")

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
            uploader = entry.get("uploader") or entry.get("channel") or entity.author
            track_field = entry.get("track")
            artist_field = entry.get("artist")
            artist, title = _parse_artist_and_title(raw_title, uploader, track_field=track_field, artist_field=artist_field)

            track_url = entry.get("webpage_url") or entry.get("url") or ""
            video_id = str(entry.get("id") or "")
            if not track_url and video_id:
                track_url = f"https://www.youtube.com/watch?v={video_id}"
            elif track_url and not track_url.startswith("http"):
                track_url = f"https://www.youtube.com/watch?v={track_url}"

            duration = int(entry.get("duration") or 0) or None
            cover = _extract_yt_thumbnail(entry, entity.cover_url)

            tracks.append(
                TrackMetadata(
                    provider_name=self.name,
                    url=track_url or f"{entity.url}#{idx}",
                    title=title,
                    artist=artist,
                    album=entity.title,
                    duration=duration,
                    cover_url=cover,
                    track_number=idx,
                    external_id=video_id or str(idx),
                    extra={"uploader": uploader},
                )
            )

        return tracks

    async def download_track(
        self,
        track_meta: TrackMetadata,
        temp_dir: str,
        progress_hook: Optional[Callable[[int], None]] = None,
    ) -> DownloadedAudio:
        """Download track to MP3 320kbps and fetch high quality cover artwork."""
        os.makedirs(temp_dir, exist_ok=True)
        out_template = os.path.join(temp_dir, "audio.%(ext)s")

        def _yt_progress(d):
            if not progress_hook:
                return
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes") or 0
                if total > 0:
                    pct = min(99, max(0, int((downloaded / total) * 100)))
                    try:
                        progress_hook(pct)
                    except Exception:
                        pass
            elif d.get("status") == "finished":
                try:
                    progress_hook(100)
                except Exception:
                    pass

        def _download():
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": out_template,
                "concurrent_fragment_downloads": 5,
                "color": "never",
                "progress_hooks": [_yt_progress] if progress_hook else [],
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
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(track_meta.url, download=True)

        await asyncio.to_thread(_download)

        expected_audio = os.path.join(temp_dir, "audio.mp3")
        if not os.path.exists(expected_audio):
            for f in os.listdir(temp_dir):
                if f.lower().endswith((".mp3", ".m4a", ".opus", ".ogg")):
                    expected_audio = os.path.join(temp_dir, f)
                    break

        if not os.path.exists(expected_audio):
            raise FileNotFoundError(f"Failed to download audio for track: {track_meta.title}")

        file_size = os.path.getsize(expected_audio)

        # Download cover artwork if present
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
                logger.warning(f"[YouTube] Cover download failed for {track_meta.title}: {e}")
                cover_path = None

        return DownloadedAudio(
            audio_path=expected_audio,
            cover_path=cover_path,
            metadata=track_meta,
            file_size=file_size,
            mime_type="audio/mpeg",
        )

    async def search(self, query: str, limit: int = 30) -> List[TrackMetadata]:
        """
        Search tracks by keyword on YouTube Music (with fallback to general YouTube search).
        """
        clean_q = query.strip()
        if not clean_q:
            return []

        def _search_ytm():
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "skip_download": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 1. Try YouTube Music search prefix
                try:
                    res = ydl.extract_info(f"ytmsearch{limit}:{clean_q}", download=False)
                    entries = res.get("entries") or []
                    if entries:
                        return entries
                except Exception as ytm_err:
                    logger.debug(f"[YouTube] ytmsearch failed, falling back to ytsearch: {ytm_err}")

                # 2. Fallback to standard YouTube search
                res = ydl.extract_info(f"ytsearch{limit}:{clean_q}", download=False)
                return res.get("entries") or []

        try:
            entries = await asyncio.to_thread(_search_ytm)
        except Exception as e:
            logger.warning(f"[YouTube] Search failed for '{clean_q}': {e}")
            return []

        results: List[TrackMetadata] = []
        for idx, entry in enumerate(entries, start=1):
            if not isinstance(entry, dict):
                continue

            raw_title = entry.get("title") or "YouTube Track"
            uploader = entry.get("uploader") or entry.get("channel") or "YouTube"
            track_field = entry.get("track")
            artist_field = entry.get("artist")
            artist, title = _parse_artist_and_title(raw_title, uploader, track_field=track_field, artist_field=artist_field)

            vid = str(entry.get("id") or "")
            t_url = entry.get("webpage_url") or entry.get("url") or f"https://www.youtube.com/watch?v={vid}"
            dur = int(entry.get("duration") or 0) or None
            cover = _extract_yt_thumbnail(entry)

            results.append(
                TrackMetadata(
                    provider_name=self.name,
                    url=t_url,
                    title=title,
                    artist=artist,
                    duration=dur,
                    cover_url=cover,
                    track_number=idx,
                    external_id=vid,
                    extra={"uploader": uploader},
                )
            )

        return results

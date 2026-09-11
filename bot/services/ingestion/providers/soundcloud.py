"""
TG Player - SoundCloud Provider
Extracts metadata and audio from SoundCloud tracks, playlists, and sets using yt-dlp.
"""
import os
import re
import asyncio
import logging
import aiohttp
from typing import Optional, List, Dict, Any

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

        info = await asyncio.to_thread(_extract)
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
                ydl.download([track_meta.url])

        await asyncio.to_thread(_download)

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

    async def search(self, query: str, limit: int = 30) -> List[TrackMetadata]:
        """Search SoundCloud for tracks matching query."""
        clean_query = query.strip()
        if not clean_query:
            return []

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
        return results

"""
TG Player - Unified Audio Sourcing Engine
Finds and downloads unencrypted high-quality audio streams matching
metadata (artist, title, duration) for Spotify tracks and SoundCloud DRM fallbacks.
"""
import os
import re
import logging
import asyncio
import tempfile
from typing import Optional, List, Set, Callable

import aiohttp
import yt_dlp

from shared.matching import (
    clean_track_metadata,
    fuzzy_match_artist,
    fuzzy_match_title,
    ARTIST_MATCH_THRESHOLD,
    TITLE_MATCH_THRESHOLD,
)
from .base import TrackMetadata, DownloadedAudio

logger = logging.getLogger(__name__)


class AudioResolver:
    """
    Resolves an unencrypted audio stream for any given TrackMetadata,
    matching duration, artist, and title, and downloads it in 320kbps MP3.
    """

    MAX_DURATION_DIFF_SECONDS = 15

    async def resolve_and_download(
        self,
        track_meta: TrackMetadata,
        temp_dir: str,
        exclude_urls: Optional[Set[str]] = None,
        progress_hook: Optional[Callable[[int], None]] = None,
    ) -> DownloadedAudio:
        """
        Find an alternative unencrypted audio stream matching the track,
        download it at 320kbps MP3, and tag it with original metadata and cover.
        """
        os.makedirs(temp_dir, exist_ok=True)
        exclude_set = exclude_urls or set()
        if track_meta.url:
            exclude_set.add(track_meta.url)

        # 1. Search candidates via SoundCloud
        search_query = f"{track_meta.artist} {track_meta.title}".strip()
        candidates = await self._search_candidates(search_query, limit=10)

        # 2. Score and pick best candidate
        best_candidate = self._pick_best_candidate(track_meta, candidates, exclude_set)

        if not best_candidate:
            # Fallback search with title only if artist had multiple collaborators
            first_artist = track_meta.artist.split(",")[0].split(" feat")[0].split(" ft")[0].strip()
            if first_artist != track_meta.artist:
                alt_query = f"{first_artist} {track_meta.title}".strip()
                more_candidates = await self._search_candidates(alt_query, limit=10)
                best_candidate = self._pick_best_candidate(track_meta, more_candidates, exclude_set)

        if not best_candidate:
            raise ValueError(
                f"Не удалось найти доступный незашифрованный аудиопоток для '{track_meta.artist} - {track_meta.title}'."
            )

        logger.info(
            f"[AudioResolver] Matched '{track_meta.artist} - {track_meta.title}' "
            f"-> candidate '{best_candidate.get('title')}' ({best_candidate.get('url')})"
        )

        # 3. Download audio stream
        audio_path = await self._download_stream(best_candidate["url"], temp_dir, progress_hook=progress_hook)

        # 4. Download high-quality cover artwork if available
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
                logger.warning(f"[AudioResolver] Failed to download cover for {track_meta.title}: {e}")
                cover_path = None

        file_size = os.path.getsize(audio_path)

        return DownloadedAudio(
            audio_path=audio_path,
            cover_path=cover_path,
            metadata=track_meta,
            file_size=file_size,
            mime_type="audio/mpeg",
        )

    async def _search_candidates(self, query: str, limit: int = 10) -> List[dict]:
        """Search SoundCloud for potential unencrypted candidate streams."""
        def _search():
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "skip_download": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                res = ydl.extract_info(f"scsearch{limit}:{query}", download=False)
                return res.get("entries") or []

        try:
            return await asyncio.to_thread(_search)
        except Exception as e:
            logger.warning(f"[AudioResolver] Candidate search failed for '{query}': {e}")
            return []

    def _pick_best_candidate(
        self,
        target: TrackMetadata,
        candidates: List[dict],
        exclude_urls: Set[str],
    ) -> Optional[dict]:
        """Score candidates based on duration match and title similarity."""
        valid_candidates = []

        for c in candidates:
            if not isinstance(c, dict):
                continue
            cand_url = c.get("webpage_url") or c.get("url") or ""
            if not cand_url or cand_url in exclude_urls:
                continue

            cand_dur = int(c.get("duration") or 0)
            cand_title = c.get("title") or ""

            # Check duration difference
            if target.duration and cand_dur:
                diff = abs(cand_dur - target.duration)
                if diff > self.MAX_DURATION_DIFF_SECONDS:
                    continue
            else:
                diff = 10  # neutral penalty if duration unknown

            # Check title similarity
            title_score = fuzzy_match_title(target.title, cand_title)
            if title_score < 0.35 and target.title.lower() not in cand_title.lower():
                continue

            # Total penalty: lower is better
            total_penalty = diff + (1.0 - title_score) * 20
            valid_candidates.append((total_penalty, c))

        if not valid_candidates:
            return None

        # Sort by best (lowest penalty)
        valid_candidates.sort(key=lambda x: x[0])
        return valid_candidates[0][1]

    async def _download_stream(
        self,
        url: str,
        temp_dir: str,
        progress_hook: Optional[Callable[[int], None]] = None,
    ) -> str:
        """Download candidate audio stream to MP3 at 320kbps."""
        out_template = os.path.join(temp_dir, "resolved_audio.%(ext)s")

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

        def _dl():
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
                ydl.download([url])

        await asyncio.to_thread(_dl)

        expected_audio = os.path.join(temp_dir, "resolved_audio.mp3")
        if not os.path.exists(expected_audio):
            for f in os.listdir(temp_dir):
                if f.lower().endswith((".mp3", ".m4a", ".opus", ".ogg")):
                    expected_audio = os.path.join(temp_dir, f)
                    break

        if not os.path.exists(expected_audio):
            raise FileNotFoundError(f"Failed to extract audio from resolved stream: {url}")

        return expected_audio


# Global singleton instance
audio_resolver = AudioResolver()

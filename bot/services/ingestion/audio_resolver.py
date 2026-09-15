"""
TG Player - Unified Audio Sourcing Engine
Finds and downloads unencrypted high-quality audio streams matching
metadata (artist, title, duration) for Spotify tracks, SoundCloud DRM fallbacks,
and YouTube Music fallback audio sourcing.
"""
import os
import re
import logging
import asyncio
import tempfile
from typing import Optional, List, Set, Callable, Tuple

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
    Features candidate retry loop and automatic fallback to YouTube Music on DRM.
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
        Tries SoundCloud candidates with retry loop, then falls back to YouTube Music.
        """
        os.makedirs(temp_dir, exist_ok=True)
        exclude_set = set(exclude_urls or set())
        if track_meta.url:
            exclude_set.add(track_meta.url)

        search_query = f"{track_meta.artist} {track_meta.title}".strip()
        downloaded_audio_path = None
        matched_candidate_title = None
        matched_candidate_url = None

        # =========================================================================
        # PHASE 1: Try SoundCloud candidates (with retry loop over multiple entries)
        # =========================================================================
        sc_candidates = await self._search_candidates(search_query, limit=10)
        ranked_sc = self._rank_candidates(track_meta, sc_candidates, exclude_set)

        if not ranked_sc:
            first_artist = track_meta.artist.split(",")[0].split(" feat")[0].split(" ft")[0].strip()
            if first_artist != track_meta.artist:
                alt_query = f"{first_artist} {track_meta.title}".strip()
                more_sc = await self._search_candidates(alt_query, limit=10)
                ranked_sc = self._rank_candidates(track_meta, more_sc, exclude_set)

        for cand in ranked_sc:
            cand_url = cand.get("webpage_url") or cand.get("url")
            cand_title = cand.get("title") or "SoundCloud Track"
            try:
                logger.info(
                    f"[AudioResolver] Trying SoundCloud candidate for '{track_meta.artist} - {track_meta.title}': "
                    f"'{cand_title}' ({cand_url})"
                )
                downloaded_audio_path = await self._download_stream(cand_url, temp_dir, progress_hook=progress_hook)
                matched_candidate_title = cand_title
                matched_candidate_url = cand_url
                break
            except Exception as e:
                err_clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', str(e))
                logger.warning(f"[AudioResolver] SoundCloud candidate '{cand_title}' failed: {err_clean}. Trying next candidate...")

        # =========================================================================
        # PHASE 2: Fallback to YouTube Music / YouTube
        # =========================================================================
        if not downloaded_audio_path:
            logger.info(
                f"[AudioResolver] SoundCloud candidates unavailable or DRM-protected for "
                f"'{track_meta.artist} - {track_meta.title}'. Falling back to YouTube Music..."
            )
            yt_candidates = await self._search_youtube_candidates(search_query, limit=6)
            ranked_yt = self._rank_candidates(track_meta, yt_candidates, exclude_set)

            if not ranked_yt and first_artist != track_meta.artist:
                alt_query = f"{first_artist} {track_meta.title}".strip()
                more_yt = await self._search_youtube_candidates(alt_query, limit=6)
                ranked_yt = self._rank_candidates(track_meta, more_yt, exclude_set)

            for cand in ranked_yt:
                cand_url = cand.get("webpage_url") or cand.get("url")
                if not cand_url and cand.get("id"):
                    cand_url = f"https://www.youtube.com/watch?v={cand['id']}"
                cand_title = cand.get("title") or "YouTube Track"
                try:
                    logger.info(
                        f"[AudioResolver] Trying YouTube candidate for '{track_meta.artist} - {track_meta.title}': "
                        f"'{cand_title}' ({cand_url})"
                    )
                    downloaded_audio_path = await self._download_stream(cand_url, temp_dir, progress_hook=progress_hook)
                    matched_candidate_title = cand_title
                    matched_candidate_url = cand_url
                    break
                except Exception as e:
                    err_clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', str(e))
                    logger.warning(f"[AudioResolver] YouTube candidate '{cand_title}' failed: {err_clean}. Trying next candidate...")

        if not downloaded_audio_path or not os.path.exists(downloaded_audio_path):
            raise ValueError(
                f"Не удалось найти доступный незашифрованный аудиопоток для '{track_meta.artist} - {track_meta.title}'."
            )

        logger.info(
            f"[AudioResolver] Successfully sourced audio for '{track_meta.artist} - {track_meta.title}' "
            f"via '{matched_candidate_title}' ({matched_candidate_url})"
        )

        # Download high-quality cover artwork if available
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

        file_size = os.path.getsize(downloaded_audio_path)

        return DownloadedAudio(
            audio_path=downloaded_audio_path,
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
            logger.warning(f"[AudioResolver] SoundCloud candidate search failed for '{query}': {e}")
            return []

    async def _search_youtube_candidates(self, query: str, limit: int = 6) -> List[dict]:
        """Search YouTube / YouTube Music for potential candidate streams."""
        def _search_yt():
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "skip_download": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    res = ydl.extract_info(f"ytmsearch{limit}:{query}", download=False)
                    entries = res.get("entries") or []
                    if entries:
                        return entries
                except Exception as ytm_err:
                    logger.debug(f"[AudioResolver] ytmsearch failed, falling back to ytsearch: {ytm_err}")

                res = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
                return res.get("entries") or []

        try:
            return await asyncio.to_thread(_search_yt)
        except Exception as e:
            logger.warning(f"[AudioResolver] YouTube candidate search failed for '{query}': {e}")
            return []

    def _rank_candidates(
        self,
        target: TrackMetadata,
        candidates: List[dict],
        exclude_urls: Set[str],
    ) -> List[dict]:
        """Score candidates based on duration match and title similarity, returning sorted list."""
        valid_candidates: List[Tuple[float, dict]] = []

        for c in candidates:
            if not isinstance(c, dict):
                continue
            cand_url = c.get("webpage_url") or c.get("url") or ""
            if not cand_url and c.get("id"):
                cand_url = f"https://www.youtube.com/watch?v={c['id']}"

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

        valid_candidates.sort(key=lambda x: x[0])
        return [c for _, c in valid_candidates]

    def _pick_best_candidate(
        self,
        target: TrackMetadata,
        candidates: List[dict],
        exclude_urls: Set[str],
    ) -> Optional[dict]:
        """Score candidates and return the single best one (for backwards compatibility)."""
        ranked = self._rank_candidates(target, candidates, exclude_urls)
        return ranked[0] if ranked else None

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

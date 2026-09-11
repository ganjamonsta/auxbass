"""
TG Player - Spotify Music Provider
Supports Spotify tracks, albums, playlists, public profiles, and personal account
likes syncing via browser session token (sp_dc) or public embed parser.
"""
import os
import re
import json
import logging
import asyncio
import tempfile
from typing import Optional, List, Tuple, Dict, Any

import aiohttp

from shared.matching import clean_track_metadata
from ..base import (
    BaseMusicProvider,
    EntityType,
    SourceEntity,
    TrackMetadata,
    DownloadedAudio,
)
from ..audio_resolver import audio_resolver

logger = logging.getLogger(__name__)


class SpotifyProvider(BaseMusicProvider):
    name: str = "spotify"

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    # Match: open.spotify.com/track/..., /album/..., /playlist/..., /user/...
    # or URI: spotify:track:..., spotify:album:..., spotify:playlist:...
    URL_PATTERN = re.compile(
        r"(?:https?://(?:open|play)\.spotify\.com/(?:intl-[a-z]{2}/)?(track|album|playlist|user)/([a-zA-Z0-9]+)|spotify:(track|album|playlist|user):([a-zA-Z0-9]+))"
    )

    def can_handle(self, url: str) -> bool:
        return bool(self.URL_PATTERN.search(url.strip()))

    def _parse_url(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract (entity_type, entity_id) from Spotify URL or URI."""
        m = self.URL_PATTERN.search(url.strip())
        if not m:
            return None, None
        etype = m.group(1) or m.group(3)
        eid = m.group(2) or m.group(4)
        return etype, eid

    async def _fetch_embed_data(self, entity_type: str, entity_id: str) -> dict:
        """Fetch and extract __NEXT_DATA__ JSON from public Spotify embed page."""
        embed_url = f"https://open.spotify.com/embed/{entity_type}/{entity_id}"
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(embed_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 404:
                    raise ValueError(f"Spotify {entity_type} '{entity_id}' не найден (404).")
                if resp.status != 200:
                    raise ValueError(f"Не удалось загрузить страницу Spotify ({resp.status}).")
                html = await resp.text()

        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if not m:
            raise ValueError("Не удалось извлечь метаданные со страницы Spotify.")

        data = json.loads(m.group(1))
        entity = (
            data.get("props", {})
            .get("pageProps", {})
            .get("state", {})
            .get("data", {})
            .get("entity", {})
        )
        return entity

    async def resolve_entity(self, url: str) -> SourceEntity:
        """Inspect Spotify URL and return metadata with track count and artwork."""
        etype_str, eid = self._parse_url(url)
        if not etype_str or not eid:
            raise ValueError("Некорректная ссылка Spotify")

        if etype_str == "track":
            etype = EntityType.TRACK
        elif etype_str == "album":
            etype = EntityType.ALBUM
        elif etype_str == "playlist":
            etype = EntityType.PLAYLIST
        else:
            raise ValueError(f"Тип сущности Spotify '{etype_str}' пока не поддерживается.")

        entity_data = await self._fetch_embed_data(etype_str, eid)

        title = entity_data.get("title") or entity_data.get("name") or "Spotify Item"
        author = None
        artists = entity_data.get("artists") or []
        if artists:
            author = ", ".join(a.get("name") for a in artists if isinstance(a, dict) and a.get("name"))
        elif entity_data.get("subtitle"):
            author = entity_data.get("subtitle")

        # Extract best cover artwork
        cover_url = None
        images = (
            entity_data.get("visualIdentity", {}).get("image")
            or entity_data.get("images")
            or entity_data.get("album", {}).get("images")
            or []
        )
        if isinstance(images, list) and images:
            # Pick largest
            sorted_imgs = sorted(images, key=lambda x: x.get("maxWidth") or x.get("width") or 0, reverse=True)
            cover_url = sorted_imgs[0].get("url")

        track_list = entity_data.get("trackList") or []
        track_count = len(track_list) if etype != EntityType.TRACK else 1

        clean_url = f"https://open.spotify.com/{etype_str}/{eid}"

        return SourceEntity(
            provider_name=self.name,
            entity_type=etype,
            url=clean_url,
            title=title,
            author=author,
            cover_url=cover_url,
            track_count=track_count,
            raw_data=entity_data,
        )

    async def fetch_tracklist(self, entity: SourceEntity) -> List[TrackMetadata]:
        """Fetch list of all tracks from the Spotify entity."""
        raw = entity.raw_data or {}

        if entity.entity_type == EntityType.TRACK:
            title = raw.get("title") or raw.get("name") or entity.title
            artists = raw.get("artists") or []
            artist_name = ", ".join(a.get("name") for a in artists if a.get("name")) if artists else entity.author or "Artist"
            dur_ms = raw.get("duration") or 0
            duration = int(dur_ms / 1000) if dur_ms else None

            return [
                TrackMetadata(
                    provider_name=self.name,
                    url=entity.url,
                    title=title,
                    artist=artist_name,
                    album=raw.get("album", {}).get("name"),
                    duration=duration,
                    cover_url=entity.cover_url,
                    external_id=str(raw.get("id") or ""),
                )
            ]

        # Album or Playlist
        track_list = raw.get("trackList") or []
        tracks: List[TrackMetadata] = []

        for idx, item in enumerate(track_list, start=1):
            if not isinstance(item, dict):
                continue

            t_title = item.get("title") or f"Track {idx}"
            t_artist = item.get("subtitle") or entity.author or "Artist"
            dur_ms = item.get("duration") or 0
            duration = int(dur_ms / 1000) if dur_ms else None
            uri = item.get("uri") or ""
            t_id = uri.split(":")[-1] if ":" in uri else str(item.get("id") or idx)
            t_url = f"https://open.spotify.com/track/{t_id}" if t_id else f"{entity.url}#{idx}"

            tracks.append(
                TrackMetadata(
                    provider_name=self.name,
                    url=t_url,
                    title=t_title,
                    artist=t_artist,
                    album=entity.title if entity.entity_type == EntityType.ALBUM else None,
                    duration=duration,
                    cover_url=entity.cover_url,
                    track_number=idx,
                    external_id=t_id,
                )
            )

        return tracks

    async def download_track(self, track_meta: TrackMetadata, temp_dir: str) -> DownloadedAudio:
        """
        Download track using the Audio Sourcing Engine.
        Matches unencrypted audio streams, applies 320kbps MP3 conversion,
        and saves official high-resolution artwork.
        """
        return await audio_resolver.resolve_and_download(track_meta, temp_dir)

    async def search(self, query: str, limit: int = 30) -> List[TrackMetadata]:
        """
        Search tracks by keyword.
        Uses SoundCloud provider search for high-fidelity streamable catalog.
        """
        from .soundcloud import SoundCloudProvider
        sc = SoundCloudProvider()
        results = await sc.search(query, limit=limit)
        # Re-tag provider as spotify-compatible search item
        return [
            TrackMetadata(
                provider_name=self.name,
                url=r.url,
                title=r.title,
                artist=r.artist,
                duration=r.duration,
                cover_url=r.cover_url,
                external_id=r.external_id,
            )
            for r in results
        ]

    # ============== Spotify Account Connection & Likes Sync ==============

    async def _get_access_token_from_sp_dc(self, sp_dc: str) -> Tuple[str, Optional[str]]:
        """
        Exchange browser cookie sp_dc for an authorized user accessToken,
        or accept direct Bearer accessToken (starts with BQ...).
        Returns (access_token, user_client_id).
        """
        raw = sp_dc.strip().strip('"').strip("'")
        if raw.startswith("Bearer "):
            raw = raw[7:].strip()

        # If user directly provided an Access Token (starts with BQ...)
        if raw.startswith("BQ") or (len(raw) > 100 and "=" not in raw and "_" not in raw[:30]):
            return raw, None

        token_url = "https://open.spotify.com/get_access_token?reason=transport&productType=web_player"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Cookie": f"sp_dc={raw}",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://open.spotify.com/",
            "Origin": "https://open.spotify.com",
            "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "app-platform": "WebPlayer",
            "spotify-app-version": "1.2.37.525.g980753d0",
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(token_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise ValueError(
                        f"Spotify отклонил сессию (HTTP {resp.status}). "
                        f"Если вы ввели sp_dc, попробуйте скопировать Access Token напрямую из консоли браузера на open.spotify.com: "
                        f"copy((await (await fetch('/get_access_token?reason=transport&productType=web_player')).json()).accessToken)"
                    )
                data = await resp.json()

        access_token = data.get("accessToken")
        is_anonymous = data.get("isAnonymous", True)
        if not access_token or is_anonymous:
            raise ValueError(
                "Недействительный токен sp_dc или сессия истекла. "
                "Пожалуйста, скопируйте свежее значение токена из браузера."
            )

        client_id = data.get("clientId")
        return access_token, client_id

    async def resolve_user_profile(
        self, username_or_url: str, auth_token: Optional[str] = None
    ) -> dict:
        """
        Resolve Spotify user profile.
        If auth_token (sp_dc) is supplied, fetches user's authenticated profile (/v1/me)
        and liked tracks count.
        """
        raw = username_or_url.strip()
        user_id = raw
        if "spotify.com/user/" in raw:
            m = re.search(r"spotify\.com/user/([a-zA-Z0-9_\-]+)", raw)
            if m:
                user_id = m.group(1)

        # If user provided sp_dc token, fetch real Spotify user profile
        if auth_token and auth_token.strip():
            access_token, _ = await self._get_access_token_from_sp_dc(auth_token)
            api_headers = {
                "Authorization": f"Bearer {access_token}",
                "User-Agent": self.USER_AGENT,
            }

            async with aiohttp.ClientSession(headers=api_headers) as session:
                async with session.get("https://api.spotify.com/v1/me") as resp:
                    if resp.status != 200:
                        raise ValueError(f"Ошибка запроса профиля Spotify (/v1/me): HTTP {resp.status}")
                    user_data = await resp.json()

                # Get liked tracks count
                likes_count = 0
                async with session.get("https://api.spotify.com/v1/me/tracks?limit=1") as resp_likes:
                    if resp_likes.status == 200:
                        likes_data = await resp_likes.json()
                        likes_count = likes_data.get("total", 0)

            ext_id = str(user_data.get("id") or user_id)
            display_name = user_data.get("display_name") or ext_id
            images = user_data.get("images") or []
            avatar_url = images[0].get("url") if images else None
            profile_url = (
                user_data.get("external_urls", {}).get("spotify")
                or f"https://open.spotify.com/user/{ext_id}"
            )

            return {
                "external_id": ext_id,
                "username": ext_id,
                "display_name": display_name,
                "profile_url": profile_url,
                "avatar_url": avatar_url,
                "likes_count": likes_count,
                "tracks_count": 0,
                "auth_token": auth_token.strip(),
            }

        # Public resolution fallback
        return {
            "external_id": user_id,
            "username": user_id,
            "display_name": user_id,
            "profile_url": f"https://open.spotify.com/user/{user_id}",
            "avatar_url": None,
            "likes_count": 0,
            "tracks_count": 0,
            "auth_token": None,
        }

    async def fetch_user_likes(
        self,
        user_id_or_username: str,
        limit: int = 50,
        next_href: Optional[str] = None,
        auth_token: Optional[str] = None,
    ) -> Tuple[List[TrackMetadata], Optional[str]]:
        """
        Fetch user's Spotify Liked Songs (/v1/me/tracks).
        Requires auth_token (sp_dc session cookie).
        """
        if not auth_token:
            raise ValueError(
                "Для синхронизации лайков Spotify требуется токен сессии (sp_dc). "
                "Укажите его в настройках подключения Spotify."
            )

        access_token, _ = await self._get_access_token_from_sp_dc(auth_token)
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": self.USER_AGENT,
        }

        req_url = next_href or f"https://api.spotify.com/v1/me/tracks?limit={min(limit, 50)}"

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(req_url) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise ValueError(f"Spotify API error ({resp.status}): {text[:100]}")
                data = await resp.json()

        items = data.get("items") or []
        next_url = data.get("next")

        tracks: List[TrackMetadata] = []
        for it in items:
            if not isinstance(it, dict):
                continue
            tr = it.get("track")
            if not isinstance(tr, dict) or not tr.get("name"):
                continue

            name = tr.get("name")
            artists = tr.get("artists") or []
            artist_name = ", ".join(a.get("name") for a in artists if a.get("name")) or "Artist"
            dur_ms = tr.get("duration_ms") or 0
            duration = int(dur_ms / 1000) if dur_ms else None

            album = tr.get("album") or {}
            images = album.get("images") or []
            cover_url = images[0].get("url") if images else None

            t_id = tr.get("id") or ""
            track_url = (
                tr.get("external_urls", {}).get("spotify")
                or f"https://open.spotify.com/track/{t_id}"
            )

            tracks.append(
                TrackMetadata(
                    provider_name=self.name,
                    url=track_url,
                    title=name,
                    artist=artist_name,
                    album=album.get("name"),
                    duration=duration,
                    cover_url=cover_url,
                    external_id=str(t_id),
                    extra={"liked_at": it.get("added_at")},
                )
            )

        return tracks, next_url

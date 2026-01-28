#!/usr/bin/env python3
"""
Исправление неполных альбомов во всей медиатеке

Этот скрипт:
1. Находит треки со статусом COMPLETED но без album_name
2. Ищет их в треклистах альбомов их артиста (через Last.fm)
3. Обновляет enrichment с правильным album_name и cover_url
4. Добавляет треки в album_tracks

Использование:
    python scripts/fix_incomplete_albums.py --dry-run          # Симуляция
    python scripts/fix_incomplete_albums.py --artist "Bladee"  # Только один артист
    python scripts/fix_incomplete_albums.py --limit 100        # Лимит треков
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import aiohttp
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from shared.database import get_session
from shared.config import Settings
from shared.models import Track, TrackEnrichment, Album, AlbumTrack, EnrichmentStatus
from shared.matching import normalize_title, normalize_artist, fuzzy_match_title

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

settings = Settings()


class AlbumFixer:
    """Исправление неполных альбомов"""
    
    LASTFM_API = "https://ws.audioscrobbler.com/2.0/"
    RATE_LIMIT = 0.25
    
    def __init__(self):
        self._session = None
        self._cache = {}
        self._last_request = 0
    
    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )
        return self._session
    
    async def _rate_limit(self):
        import time
        now = time.time()
        elapsed = now - self._last_request
        if elapsed < self.RATE_LIMIT:
            await asyncio.sleep(self.RATE_LIMIT - elapsed)
        self._last_request = time.time()
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def get_artist_albums(self, artist: str, limit: int = 30) -> list:
        """Получить список альбомов артиста из Last.fm"""
        cache_key = f"albums:{normalize_artist(artist)}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        if not settings.lastfm_api_key:
            return []
        
        await self._rate_limit()
        session = await self._get_session()
        
        try:
            params = {
                'method': 'artist.gettopalbums',
                'artist': artist,
                'limit': limit,
                'api_key': settings.lastfm_api_key,
                'format': 'json'
            }
            
            async with session.get(self.LASTFM_API, params=params) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
            
            albums = data.get('topalbums', {}).get('album', [])
            if isinstance(albums, dict):
                albums = [albums]
            
            result = []
            for a in albums:
                name = a.get('name', '')
                if name and name.lower() not in ['(null)', 'none', '']:
                    images = a.get('image', [])
                    cover = None
                    for img in reversed(images if isinstance(images, list) else [images]):
                        if img.get('#text'):
                            cover = img['#text']
                            break
                    result.append({
                        'name': name,
                        'artist': a.get('artist', {}).get('name', artist),
                        'cover_url': cover
                    })
            
            self._cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.debug(f"Last.fm error: {e}")
            return []
    
    async def get_album_tracklist(self, artist: str, album: str) -> dict:
        """Получить треклист альбома из Last.fm"""
        cache_key = f"tracklist:{normalize_artist(artist)}|{normalize_title(album)}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        if not settings.lastfm_api_key:
            return {}
        
        await self._rate_limit()
        session = await self._get_session()
        
        try:
            params = {
                'method': 'album.getinfo',
                'artist': artist,
                'album': album,
                'api_key': settings.lastfm_api_key,
                'format': 'json'
            }
            
            async with session.get(self.LASTFM_API, params=params) as resp:
                if resp.status != 200:
                    return {}
                data = await resp.json()
            
            if 'album' not in data:
                return {}
            
            album_data = data['album']
            
            # Обложка
            images = album_data.get('image', [])
            cover_url = None
            for img in reversed(images if isinstance(images, list) else [images]):
                if img.get('#text'):
                    cover_url = img['#text']
                    break
            
            # Треки
            tracks = album_data.get('tracks', {}).get('track', [])
            if isinstance(tracks, dict):
                tracks = [tracks]
            
            result = {
                'name': album_data.get('name', album),
                'artist': album_data.get('artist', artist),
                'cover_url': cover_url,
                'tracks': [
                    {
                        'name': t.get('name'),
                        'normalized': normalize_title(t.get('name', '')),
                        'number': i + 1
                    }
                    for i, t in enumerate(tracks) if t.get('name')
                ]
            }
            
            self._cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.debug(f"Last.fm error: {e}")
            return {}
    
    async def find_album_for_track(self, track_title: str, artist: str) -> dict:
        """Найти альбом для трека через поиск в треклистах"""
        track_norm = normalize_title(track_title)
        
        # Получить альбомы артиста
        albums = await self.get_artist_albums(artist)
        
        for album_info in albums:
            tracklist = await self.get_album_tracklist(artist, album_info['name'])
            
            if not tracklist or not tracklist.get('tracks'):
                continue
            
            # Точное совпадение
            for t in tracklist['tracks']:
                if track_norm == t['normalized']:
                    return {
                        'album_name': tracklist['name'],
                        'cover_url': tracklist.get('cover_url'),
                        'track_number': t['number']
                    }
            
            # Fuzzy matching
            for t in tracklist['tracks']:
                if fuzzy_match_title(track_title, t['name']) >= 0.8:
                    return {
                        'album_name': tracklist['name'],
                        'cover_url': tracklist.get('cover_url'),
                        'track_number': t['number']
                    }
        
        return {}
    
    async def fix_all(
        self,
        artist_filter: str = None,
        limit: int = 200,
        dry_run: bool = False
    ):
        """Исправить все треки без альбома"""
        
        print("=" * 80)
        print("ИСПРАВЛЕНИЕ НЕПОЛНЫХ АЛЬБОМОВ")
        print("=" * 80)
        
        if dry_run:
            print(">>> РЕЖИМ СИМУЛЯЦИИ <<<\n")
        
        async with get_session() as session:
            # Найти треки COMPLETED без album_name
            query = (
                select(Track)
                .options(selectinload(Track.enrichment))
                .outerjoin(TrackEnrichment, TrackEnrichment.track_id == Track.id)
                .where(
                    Track.enrichment_status == EnrichmentStatus.COMPLETED,
                    (TrackEnrichment.album_name.is_(None)) | (TrackEnrichment.id.is_(None))
                )
                .limit(limit)
            )
            
            if artist_filter:
                query = query.where(Track.artist.ilike(f"%{artist_filter}%"))
                print(f"Фильтр по артисту: {artist_filter}")
            
            result = await session.execute(query)
            tracks = result.scalars().all()
            
            print(f"Найдено треков без альбома: {len(tracks)}")
            
            if not tracks:
                print("Нет треков для обработки")
                return
            
            # Группировать по артисту
            by_artist = defaultdict(list)
            for t in tracks:
                by_artist[t.artist or "Unknown"].append(t)
            
            print(f"Артистов: {len(by_artist)}\n")
            
            fixed_count = 0
            added_to_album = 0
            
            for artist, artist_tracks in sorted(by_artist.items(), key=lambda x: -len(x[1])):
                print(f"--- {artist} ({len(artist_tracks)} треков) ---")
                
                for track in artist_tracks:
                    match = await self.find_album_for_track(track.title, artist)
                    
                    if match:
                        album_name = match['album_name']
                        cover_url = match.get('cover_url')
                        track_number = match.get('track_number')
                        
                        print(f"  + [{track.id}] {track.title}")
                        print(f"      -> {album_name} (#{track_number})")
                        
                        if not dry_run:
                            # Обновить enrichment
                            if track.enrichment:
                                track.enrichment.album_name = album_name
                                track.enrichment.track_number = track_number
                                if cover_url and not track.enrichment.cover_url:
                                    track.enrichment.cover_url = cover_url
                            else:
                                track.enrichment = TrackEnrichment(
                                    track_id=track.id,
                                    album_name=album_name,
                                    cover_url=cover_url,
                                    track_number=track_number,
                                )
                                session.add(track.enrichment)
                            
                            # Найти или создать Album
                            album_result = await session.execute(
                                select(Album).where(
                                    Album.normalized_artist == normalize_artist(artist),
                                    Album.normalized_name == normalize_title(album_name)
                                )
                            )
                            album = album_result.scalar_one_or_none()
                            
                            if album:
                                # Проверить, есть ли трек в album_tracks
                                at_result = await session.execute(
                                    select(AlbumTrack).where(
                                        AlbumTrack.album_id == album.id,
                                        AlbumTrack.track_id == track.id
                                    )
                                )
                                if not at_result.scalar_one_or_none():
                                    at = AlbumTrack(
                                        album_id=album.id,
                                        track_id=track.id,
                                        track_number=track_number or 0
                                    )
                                    session.add(at)
                                    added_to_album += 1
                        
                        fixed_count += 1
                    else:
                        print(f"  - [{track.id}] {track.title}")
            
            if not dry_run:
                await session.commit()
            
            print(f"\n{'=' * 80}")
            print(f"ИТОГО:")
            print(f"  Найдено альбомов: {fixed_count}")
            print(f"  Добавлено в album_tracks: {added_to_album}")
            if dry_run:
                print("  (симуляция - изменения НЕ сохранены)")
            print("=" * 80)


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Исправление неполных альбомов')
    parser.add_argument('--artist', '-a', type=str, help='Фильтр по артисту')
    parser.add_argument('--limit', '-l', type=int, default=200, help='Лимит треков')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Режим симуляции')
    
    args = parser.parse_args()
    
    fixer = AlbumFixer()
    try:
        await fixer.fix_all(
            artist_filter=args.artist,
            limit=args.limit,
            dry_run=args.dry_run
        )
    finally:
        await fixer.close()


if __name__ == "__main__":
    asyncio.run(main())

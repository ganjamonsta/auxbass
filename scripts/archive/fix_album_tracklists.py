#!/usr/bin/env python3
"""
Исправление треклистов альбомов

Этот скрипт:
1. Находит альбомы без full_tracklist
2. Загружает треклист из Last.fm
3. Добавляет недостающие треки в album_tracks
4. Заполняет full_tracklist для показа плейсхолдеров

Использование:
    python scripts/fix_album_tracklists.py --album "Cold Visions" --dry-run
    python scripts/fix_album_tracklists.py --album "Cold Visions"
    python scripts/fix_album_tracklists.py --limit 50
"""
import asyncio
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import aiohttp
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from shared.database import get_session
from shared.config import Settings
from shared.models import Track, TrackEnrichment, Album, AlbumTrack
from shared.matching import normalize_title, normalize_artist, fuzzy_match_title

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

settings = Settings()


class TracklistFixer:
    """Исправление full_tracklist для альбомов"""
    
    LASTFM_API = "https://ws.audioscrobbler.com/2.0/"
    RATE_LIMIT = 0.25
    
    def __init__(self):
        self._session = None
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
    
    async def get_lastfm_tracklist(self, artist: str, album: str) -> list:
        """Получить полный треклист альбома из Last.fm"""
        if not settings.lastfm_api_key:
            return []
        
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
                    return []
                data = await resp.json()
            
            if 'album' not in data:
                return []
            
            album_data = data['album']
            tracks = album_data.get('tracks', {}).get('track', [])
            
            if isinstance(tracks, dict):
                tracks = [tracks]
            
            result = []
            for i, t in enumerate(tracks):
                duration = 0
                if t.get('duration'):
                    try:
                        duration = int(t['duration'])
                    except (ValueError, TypeError):
                        pass
                
                result.append({
                    'track_number': i + 1,
                    'title': t.get('name', ''),
                    'artist': t.get('artist', {}).get('name', artist) if isinstance(t.get('artist'), dict) else artist,
                    'duration': duration,
                    'normalized': normalize_title(t.get('name', ''))
                })
            
            return result
            
        except Exception as e:
            logger.debug(f"Last.fm error: {e}")
            return []
    
    async def fix_album(
        self,
        album: Album,
        session,
        dry_run: bool = False
    ) -> dict:
        """Исправить треклист одного альбома"""
        
        result = {
            'album_id': album.id,
            'album_name': album.name,
            'artist': album.artist,
            'tracks_added': 0,
            'full_tracklist_set': False,
            'lastfm_tracks': 0,
            'album_tracks': 0,
            'missing': []
        }
        
        # Получить треклист из Last.fm
        lastfm_tracks = await self.get_lastfm_tracklist(album.artist, album.name)
        result['lastfm_tracks'] = len(lastfm_tracks)
        
        if not lastfm_tracks:
            return result
        
        # Получить текущие album_tracks
        at_result = await session.execute(
            select(AlbumTrack, Track)
            .join(Track, Track.id == AlbumTrack.track_id)
            .where(AlbumTrack.album_id == album.id)
        )
        current_tracks = at_result.all()
        result['album_tracks'] = len(current_tracks)
        
        # Создать lookup по нормализованному названию
        tracks_in_album = {}
        for at, track in current_tracks:
            norm = normalize_title(track.title or "")
            tracks_in_album[norm] = (at, track)
        
        # Найти все треки с enrichment этого альбома
        enrich_result = await session.execute(
            select(Track)
            .options(selectinload(Track.enrichment))
            .join(TrackEnrichment, TrackEnrichment.track_id == Track.id)
            .where(
                func.lower(TrackEnrichment.album_name) == album.name.lower()
            )
        )
        enriched_tracks = enrich_result.scalars().all()
        
        # Lookup по нормализованному названию
        enriched_by_title = {}
        for t in enriched_tracks:
            norm = normalize_title(t.title or "")
            if norm not in enriched_by_title:
                enriched_by_title[norm] = t
        
        # Проверить какие треки из Last.fm отсутствуют
        missing_tracks = []
        for lfm_track in lastfm_tracks:
            norm = lfm_track['normalized']
            
            # Точное совпадение
            if norm in tracks_in_album:
                continue
            
            # Fuzzy match
            found = False
            for existing_norm in tracks_in_album:
                if fuzzy_match_title(lfm_track['title'], tracks_in_album[existing_norm][1].title or "") >= 0.85:
                    found = True
                    break
            
            if not found:
                missing_tracks.append(lfm_track)
        
        result['missing'] = [t['title'] for t in missing_tracks]
        
        # Добавить недостающие треки в album_tracks если они есть в enriched
        for missing in missing_tracks:
            norm = missing['normalized']
            track = None
            
            # Точное совпадение
            if norm in enriched_by_title:
                track = enriched_by_title[norm]
            else:
                # Fuzzy match
                for enr_norm, enr_track in enriched_by_title.items():
                    if fuzzy_match_title(missing['title'], enr_track.title or "") >= 0.85:
                        track = enr_track
                        break
            
            if track:
                # Проверить что трека ещё нет в album_tracks
                existing = await session.execute(
                    select(AlbumTrack).where(
                        AlbumTrack.album_id == album.id,
                        AlbumTrack.track_id == track.id
                    )
                )
                if not existing.scalar_one_or_none():
                    if not dry_run:
                        at = AlbumTrack(
                            album_id=album.id,
                            track_id=track.id,
                            track_number=missing['track_number']
                        )
                        session.add(at)
                    result['tracks_added'] += 1
                    logger.info(f"    + Добавлен: #{missing['track_number']} {missing['title']}")
        
        # Создать full_tracklist JSON
        full_tracklist = []
        for lfm_track in lastfm_tracks:
            full_tracklist.append({
                'track_number': lfm_track['track_number'],
                'title': lfm_track['title'],
                'artist': lfm_track['artist'],
                'duration': lfm_track['duration'],
                'deezer_id': None  # Можно добавить поиск в Deezer
            })
        
        if full_tracklist and not album.full_tracklist:
            if not dry_run:
                album.full_tracklist = json.dumps(full_tracklist, ensure_ascii=False)
                album.total_tracks = len(lastfm_tracks)
            result['full_tracklist_set'] = True
            logger.info(f"    ✓ full_tracklist установлен ({len(lastfm_tracks)} треков)")
        
        return result
    
    async def fix_all(
        self,
        album_filter: str = None,
        limit: int = 50,
        dry_run: bool = False
    ):
        """Исправить все альбомы"""
        
        print("=" * 80)
        print("ИСПРАВЛЕНИЕ ТРЕКЛИСТОВ АЛЬБОМОВ")
        print("=" * 80)
        
        if dry_run:
            print(">>> РЕЖИМ СИМУЛЯЦИИ <<<\n")
        
        async with get_session() as session:
            # Найти альбомы
            query = select(Album)
            
            if album_filter:
                query = query.where(Album.name.ilike(f"%{album_filter}%"))
                print(f"Фильтр: '{album_filter}'")
            else:
                # Только альбомы без full_tracklist
                query = query.where(Album.full_tracklist.is_(None))
                print("Альбомы без full_tracklist")
            
            query = query.limit(limit)
            
            result = await session.execute(query)
            albums = result.scalars().all()
            
            print(f"Найдено альбомов: {len(albums)}\n")
            
            if not albums:
                print("Нет альбомов для обработки")
                return
            
            total_added = 0
            total_tracklists = 0
            
            for album in albums:
                print(f"--- {album.artist} - {album.name} (ID: {album.id}) ---")
                
                result = await self.fix_album(album, session, dry_run)
                
                if result['lastfm_tracks'] == 0:
                    print("    ⚠ Не найден в Last.fm")
                    continue
                
                print(f"    Last.fm: {result['lastfm_tracks']} треков")
                print(f"    album_tracks: {result['album_tracks']} треков")
                
                if result['missing']:
                    print(f"    Отсутствуют в album_tracks:")
                    for m in result['missing'][:5]:
                        print(f"      - {m}")
                    if len(result['missing']) > 5:
                        print(f"      ... и ещё {len(result['missing']) - 5}")
                
                total_added += result['tracks_added']
                if result['full_tracklist_set']:
                    total_tracklists += 1
            
            if not dry_run:
                await session.commit()
            
            print(f"\n{'=' * 80}")
            print(f"ИТОГО:")
            print(f"  Добавлено треков: {total_added}")
            print(f"  Установлено full_tracklist: {total_tracklists}")
            if dry_run:
                print("  (симуляция - изменения НЕ сохранены)")
            print("=" * 80)


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Исправление треклистов альбомов')
    parser.add_argument('--album', '-a', type=str, help='Фильтр по названию альбома')
    parser.add_argument('--limit', '-l', type=int, default=50, help='Лимит альбомов')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Режим симуляции')
    
    args = parser.parse_args()
    
    fixer = TracklistFixer()
    try:
        await fixer.fix_all(
            album_filter=args.album,
            limit=args.limit,
            dry_run=args.dry_run
        )
    finally:
        await fixer.close()


if __name__ == "__main__":
    asyncio.run(main())

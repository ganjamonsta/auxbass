#!/usr/bin/env python3
"""
Диагностика неполных альбомов во всей медиатеке

Находит альбомы где:
1. Есть треки в библиотеке, но нет enrichment с альбомом
2. Количество треков меньше чем в Last.fm
3. Треки неправильно обогащены (album = None)

Использование:
    python scripts/diagnose_albums_full.py
    python scripts/diagnose_albums_full.py --artist "Bladee"
    python scripts/diagnose_albums_full.py --min-tracks 5
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import aiohttp
from collections import defaultdict
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from shared.database import get_session
from shared.config import Settings
from shared.models import Track, TrackEnrichment, Album, AlbumTrack, UserLibrary
from shared.matching import normalize_title, normalize_artist

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

settings = Settings()


class AlbumDiagnostics:
    """Диагностика альбомов"""
    
    LASTFM_API = "https://ws.audioscrobbler.com/2.0/"
    
    def __init__(self):
        self._session = None
        self._cache = {}
    
    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def get_lastfm_album_tracks(self, artist: str, album: str) -> list:
        """Получить треклист альбома из Last.fm"""
        cache_key = f"{normalize_artist(artist)}|{normalize_title(album)}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        if not settings.lastfm_api_key:
            return []
        
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
            
            tracks = data['album'].get('tracks', {}).get('track', [])
            if isinstance(tracks, dict):
                tracks = [tracks]
            
            result = [t.get('name') for t in tracks if t.get('name')]
            self._cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.debug(f"Last.fm error: {e}")
            return []
    
    async def diagnose_all(
        self,
        artist_filter: str = None,
        min_tracks: int = 1,
        show_details: bool = True
    ):
        """Диагностика всех альбомов"""
        
        print("=" * 80)
        print("ДИАГНОСТИКА АЛЬБОМОВ В МЕДИАТЕКЕ")
        print("=" * 80)
        
        if artist_filter:
            print(f"Фильтр по артисту: {artist_filter}")
        
        async with get_session() as session:
            # 1. Статистика по обогащению
            print("\n1. СТАТИСТИКА ОБОГАЩЕНИЯ:")
            print("-" * 40)
            
            result = await session.execute(
                select(Track.enrichment_status, func.count(Track.id))
                .group_by(Track.enrichment_status)
            )
            stats = {str(row[0]): row[1] for row in result.all()}
            for status, count in sorted(stats.items()):
                print(f"   {status}: {count}")
            
            # 2. Треки COMPLETED без album_name
            print("\n2. ТРЕКИ БЕЗ АЛЬБОМА (COMPLETED но album=None):")
            print("-" * 40)
            
            query = (
                select(Track)
                .options(selectinload(Track.enrichment))
                .outerjoin(TrackEnrichment, TrackEnrichment.track_id == Track.id)
                .where(
                    Track.enrichment_status == "completed",
                    (TrackEnrichment.album_name.is_(None)) | (TrackEnrichment.id.is_(None))
                )
            )
            
            if artist_filter:
                query = query.where(Track.artist.ilike(f"%{artist_filter}%"))
            
            result = await session.execute(query)
            tracks_no_album = result.scalars().all()
            
            # Группировать по артисту
            by_artist = defaultdict(list)
            for t in tracks_no_album:
                by_artist[t.artist or "Unknown"].append(t)
            
            print(f"   Всего треков без альбома: {len(tracks_no_album)}")
            print(f"   Артистов: {len(by_artist)}")
            
            if show_details and by_artist:
                print("\n   Топ артистов без альбомов:")
                sorted_artists = sorted(by_artist.items(), key=lambda x: -len(x[1]))[:15]
                for artist, tracks in sorted_artists:
                    print(f"      {artist}: {len(tracks)} треков")
                    if len(tracks) <= 5:
                        for t in tracks:
                            cover = "cover" if (t.enrichment and t.enrichment.cover_url) else "no cover"
                            print(f"         - {t.title} ({cover})")
            
            # 3. Альбомы в базе
            print("\n3. АЛЬБОМЫ В БАЗЕ ДАННЫХ:")
            print("-" * 40)
            
            query = select(Album)
            if artist_filter:
                query = query.where(Album.artist.ilike(f"%{artist_filter}%"))
            
            result = await session.execute(query)
            albums = result.scalars().all()
            
            print(f"   Всего альбомов: {len(albums)}")
            
            # Проверить каждый альбом
            incomplete_albums = []
            
            for album in albums:
                # Получить треки в альбоме
                result = await session.execute(
                    select(func.count(AlbumTrack.id))
                    .where(AlbumTrack.album_id == album.id)
                )
                db_count = result.scalar() or 0
                
                # Получить треклист из Last.fm
                lastfm_tracks = await self.get_lastfm_album_tracks(album.artist, album.name)
                lastfm_count = len(lastfm_tracks)
                
                if lastfm_count > 0 and db_count < lastfm_count:
                    incomplete_albums.append({
                        "album": album,
                        "db_count": db_count,
                        "lastfm_count": lastfm_count,
                        "lastfm_tracks": lastfm_tracks,
                        "missing": lastfm_count - db_count,
                        "percent": round(db_count / lastfm_count * 100) if lastfm_count else 0
                    })
            
            # Сортировать по количеству недостающих треков
            incomplete_albums.sort(key=lambda x: -x["missing"])
            
            print(f"\n4. НЕПОЛНЫЕ АЛЬБОМЫ ({len(incomplete_albums)} из {len(albums)}):")
            print("-" * 40)
            
            if not incomplete_albums:
                print("   Все альбомы полные!")
            else:
                for info in incomplete_albums[:20]:
                    album = info["album"]
                    print(f"\n   {album.artist} - {album.name}")
                    print(f"      В базе: {info['db_count']}, Last.fm: {info['lastfm_count']} ({info['percent']}%)")
                    print(f"      Не хватает: {info['missing']} треков")
                    
                    if show_details and info['missing'] <= 15:
                        # Найти какие треки отсутствуют
                        result = await session.execute(
                            select(Track.title)
                            .join(AlbumTrack, AlbumTrack.track_id == Track.id)
                            .where(AlbumTrack.album_id == album.id)
                        )
                        db_titles = {normalize_title(row[0]) for row in result.all()}
                        
                        missing = []
                        for lastfm_title in info["lastfm_tracks"]:
                            if normalize_title(lastfm_title) not in db_titles:
                                missing.append(lastfm_title)
                        
                        if missing:
                            print(f"      Отсутствуют:")
                            for m in missing[:10]:
                                print(f"         - {m}")
                            if len(missing) > 10:
                                print(f"         ... ещё {len(missing) - 10}")
            
            # 5. Поиск треков без альбома которые есть в Last.fm альбомах
            if tracks_no_album and show_details:
                print(f"\n5. ПОИСК АЛЬБОМОВ ДЛЯ ТРЕКОВ БЕЗ ENRICHMENT:")
                print("-" * 40)
                
                # Для каждого артиста с треками без альбома
                # проверить, есть ли эти треки в Last.fm альбомах
                checked = 0
                found = 0
                
                for artist, tracks in sorted(by_artist.items(), key=lambda x: -len(x[1]))[:10]:
                    if checked >= 50:
                        break
                    
                    # Получить все альбомы этого артиста которые уже есть в базе
                    artist_albums = [a for a in albums if normalize_artist(a.artist) == normalize_artist(artist)]
                    
                    for track in tracks[:10]:
                        if checked >= 50:
                            break
                        checked += 1
                        
                        track_norm = normalize_title(track.title)
                        
                        # Проверить в каждом альбоме
                        for album in artist_albums:
                            lastfm_tracks = await self.get_lastfm_album_tracks(album.artist, album.name)
                            lastfm_normalized = {normalize_title(t) for t in lastfm_tracks}
                            
                            if track_norm in lastfm_normalized:
                                print(f"   + [{track.id}] {track.title}")
                                print(f"      -> должен быть в: {album.name}")
                                found += 1
                                break
                
                print(f"\n   Проверено: {checked}, найдено альбомов: {found}")
            
            # Итоги
            print("\n" + "=" * 80)
            print("ИТОГИ:")
            print("=" * 80)
            print(f"   Всего треков: {sum(stats.values())}")
            print(f"   Треков без альбома: {len(tracks_no_album)}")
            print(f"   Альбомов в базе: {len(albums)}")
            print(f"   Неполных альбомов: {len(incomplete_albums)}")
            
            if incomplete_albums:
                total_missing = sum(a["missing"] for a in incomplete_albums)
                print(f"   Всего недостающих треков: {total_missing}")


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Диагностика альбомов в медиатеке')
    parser.add_argument('--artist', '-a', type=str, help='Фильтр по артисту')
    parser.add_argument('--min-tracks', '-m', type=int, default=1, help='Минимум треков в альбоме')
    parser.add_argument('--no-details', action='store_true', help='Не показывать детали')
    
    args = parser.parse_args()
    
    diag = AlbumDiagnostics()
    try:
        await diag.diagnose_all(
            artist_filter=args.artist,
            min_tracks=args.min_tracks,
            show_details=not args.no_details
        )
    finally:
        await diag.close()


if __name__ == "__main__":
    asyncio.run(main())

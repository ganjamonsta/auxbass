#!/usr/bin/env python3
"""
Диагностика проблемы с альбомом Cold Visions

Проверяет:
1. Все треки Bladee в библиотеке
2. Какие из них обогащены
3. Какие имеют альбом Cold Visions в enrichment
4. Какие попали в таблицу album_tracks
5. Сравнение с полным треклистом из Last.fm
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from shared.database import get_session
from shared.config import Settings
from shared.models import Track, TrackEnrichment, Album, AlbumTrack, UserLibrary
from shared.matching import normalize_artist, normalize_title


settings = Settings()


def get_lastfm_tracklist(artist: str, album: str) -> list:
    """Получить треклист альбома из Last.fm"""
    r = requests.get('https://ws.audioscrobbler.com/2.0/', params={
        'method': 'album.getinfo',
        'artist': artist,
        'album': album,
        'api_key': settings.lastfm_api_key,
        'format': 'json'
    })
    
    data = r.json()
    if 'album' not in data:
        print(f"Ошибка Last.fm: {data}")
        return []
    
    tracks = data['album'].get('tracks', {}).get('track', [])
    if isinstance(tracks, dict):
        tracks = [tracks]
    
    return [t.get('name') for t in tracks]


async def diagnose():
    """Основная диагностика"""
    
    print("=" * 80)
    print("ДИАГНОСТИКА АЛЬБОМА COLD VISIONS")
    print("=" * 80)
    
    # Получить треклист из Last.fm
    print("\n1. ТРЕКЛИСТ ИЗ LAST.FM:")
    print("-" * 40)
    lastfm_tracks = get_lastfm_tracklist("Bladee", "Cold Visions")
    print(f"   Всего треков в Last.fm: {len(lastfm_tracks)}")
    for i, t in enumerate(lastfm_tracks, 1):
        print(f"   {i:2}. {t}")
    
    lastfm_normalized = {normalize_title(t) for t in lastfm_tracks}
    
    async with get_session() as session:
        # Найти альбом Cold Visions
        print("\n2. АЛЬБОМ В БАЗЕ ДАННЫХ:")
        print("-" * 40)
        result = await session.execute(
            select(Album).where(Album.name.ilike("%Cold Visions%"))
        )
        albums = result.scalars().all()
        
        for album in albums:
            print(f"   ID: {album.id}")
            print(f"   Название: {album.name}")
            print(f"   Артист: {album.artist}")
            print(f"   Total tracks: {album.total_tracks}")
            print(f"   Deezer ID: {album.deezer_album_id}")
            print(f"   Есть full_tracklist: {album.full_tracklist is not None}")
        
        # Треки в album_tracks
        print("\n3. ТРЕКИ В ALBUM_TRACKS:")
        print("-" * 40)
        if albums:
            album_id = albums[0].id
            result = await session.execute(
                select(Track)
                .join(AlbumTrack, AlbumTrack.track_id == Track.id)
                .options(selectinload(Track.enrichment))
                .where(AlbumTrack.album_id == album_id)
                .order_by(AlbumTrack.track_number)
            )
            album_tracks = result.scalars().all()
            print(f"   Всего треков в album_tracks: {len(album_tracks)}")
            for t in album_tracks:
                cover = "✓ cover" if t.cover_url else "✗ no cover"
                print(f"   [{t.id:4}] {t.title} | {cover}")
        
        # Все треки Bladee с Cold Visions enrichment
        print("\n4. ВСЕ ТРЕКИ С ENRICHMENT 'Cold Visions':")
        print("-" * 40)
        result = await session.execute(
            select(Track)
            .join(TrackEnrichment, TrackEnrichment.track_id == Track.id)
            .options(selectinload(Track.enrichment))
            .where(TrackEnrichment.album_name.ilike("%Cold Visions%"))
        )
        enriched_tracks = result.scalars().all()
        print(f"   Всего с enrichment Cold Visions: {len(enriched_tracks)}")
        for t in enriched_tracks:
            cover = "✓ cover" if t.cover_url else "✗ no cover"
            norm = normalize_title(t.title)
            in_lastfm = "✓ в Last.fm" if norm in lastfm_normalized else "✗ НЕ в Last.fm"
            print(f"   [{t.id:4}] {t.title} - {t.artist} | {cover} | {in_lastfm}")
        
        # Все треки Bladee
        print("\n5. ВСЕ ТРЕКИ BLADEE (в библиотеке):")
        print("-" * 40)
        result = await session.execute(
            select(Track)
            .options(selectinload(Track.enrichment))
            .where(func.lower(Track.artist).like("%bladee%"))
            .order_by(Track.enrichment_status, Track.title)
        )
        all_bladee = result.scalars().all()
        print(f"   Всего треков Bladee: {len(all_bladee)}")
        
        # Группировка по статусу обогащения
        by_status = {}
        for t in all_bladee:
            status = str(t.enrichment_status)
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(t)
        
        for status, tracks in sorted(by_status.items()):
            print(f"\n   {status} ({len(tracks)} треков):")
            for t in tracks[:10]:  # Показываем первые 10
                album = t.enrichment.album_name if t.enrichment else None
                cover = "✓" if t.cover_url else "✗"
                norm = normalize_title(t.title)
                in_lastfm = "CV" if norm in lastfm_normalized else ""
                print(f"      [{t.id:4}] {t.title[:40]:<40} | album: {album or 'N/A':<20} | {cover} | {in_lastfm}")
            if len(tracks) > 10:
                print(f"      ... ещё {len(tracks) - 10} треков")
        
        # Треки из Last.fm которых нет в enrichment
        print("\n6. ТРЕКИ ИЗ LAST.FM БЕЗ ENRICHMENT 'Cold Visions':")
        print("-" * 40)
        
        enriched_normalized = {normalize_title(t.title) for t in enriched_tracks}
        
        missing_from_enrichment = []
        for track_name in lastfm_tracks:
            norm = normalize_title(track_name)
            if norm not in enriched_normalized:
                missing_from_enrichment.append(track_name)
        
        print(f"   Отсутствуют в enrichment: {len(missing_from_enrichment)}")
        for name in missing_from_enrichment:
            print(f"      - {name}")
        
        # Проверяем, есть ли эти треки в библиотеке но без enrichment
        print("\n7. ПРОВЕРКА: ЭТИ ТРЕКИ ЕСТЬ В БИБЛИОТЕКЕ?")
        print("-" * 40)
        
        all_bladee_normalized = {normalize_title(t.title): t for t in all_bladee}
        
        for track_name in missing_from_enrichment:
            norm = normalize_title(track_name)
            
            if norm in all_bladee_normalized:
                t = all_bladee_normalized[norm]
                album = t.enrichment.album_name if t.enrichment else None
                status = t.enrichment_status
                cover = "✓" if t.cover_url else "✗"
                print(f"   ✓ НАЙДЕН: '{track_name}' -> [{t.id}] {t.title}")
                print(f"      status: {status}, album: {album}, cover: {cover}")
            else:
                # Поиск по частичному совпадению
                found = False
                for bladee_norm, t in all_bladee_normalized.items():
                    if norm in bladee_norm or bladee_norm in norm:
                        album = t.enrichment.album_name if t.enrichment else None
                        status = t.enrichment_status
                        print(f"   ~ ПОХОЖ: '{track_name}' -> [{t.id}] {t.title}")
                        print(f"      status: {status}, album: {album}")
                        found = True
                        break
                if not found:
                    print(f"   ✗ НЕ НАЙДЕН: '{track_name}'")
        
        # Итоговая статистика
        print("\n" + "=" * 80)
        print("ИТОГИ ДИАГНОСТИКИ:")
        print("=" * 80)
        print(f"   Треков в Last.fm:          {len(lastfm_tracks)}")
        print(f"   Треков в album_tracks:     {len(album_tracks) if albums else 0}")
        print(f"   Треков с CV enrichment:    {len(enriched_tracks)}")
        print(f"   Всего треков Bladee в БД:  {len(all_bladee)}")
        print(f"   Треков без enrichment CV:  {len(missing_from_enrichment)}")
        
        # Статистика по статусам
        print("\n   По статусам обогащения:")
        for status, tracks in sorted(by_status.items()):
            print(f"      {status}: {len(tracks)}")


if __name__ == "__main__":
    asyncio.run(diagnose())

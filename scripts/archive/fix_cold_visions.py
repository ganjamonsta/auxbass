#!/usr/bin/env python3
"""
Исправление треков Cold Visions, которые не были правильно обогащены

Этот скрипт:
1. Получает полный треклист Cold Visions из Last.fm
2. Находит треки в библиотеке которые соответствуют этому треклисту
3. Обновляет их enrichment с правильным album_name и cover_url
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import aiohttp
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from shared.database import get_session
from shared.config import Settings
from shared.models import Track, TrackEnrichment, Album, AlbumTrack
from shared.matching import normalize_title, fuzzy_match_title

settings = Settings()


async def get_lastfm_album_info(artist: str, album: str) -> dict:
    """Получить информацию об альбоме из Last.fm"""
    async with aiohttp.ClientSession() as session:
        async with session.get('https://ws.audioscrobbler.com/2.0/', params={
            'method': 'album.getinfo',
            'artist': artist,
            'album': album,
            'api_key': settings.lastfm_api_key,
            'format': 'json'
        }) as resp:
            data = await resp.json()
    
    if 'album' not in data:
        print(f"Ошибка Last.fm: {data}")
        return {}
    
    album_data = data['album']
    
    # Извлечь обложку (самую большую)
    images = album_data.get('image', [])
    cover_url = None
    for img in reversed(images):
        if img.get('#text'):
            cover_url = img['#text']
            break
    
    # Извлечь треклист
    tracks = album_data.get('tracks', {}).get('track', [])
    if isinstance(tracks, dict):
        tracks = [tracks]
    
    return {
        'name': album_data.get('name'),
        'artist': album_data.get('artist'),
        'cover_url': cover_url,
        'tracks': [
            {
                'name': t.get('name'),
                'number': i + 1,
                'duration': int(t.get('duration', 0))
            }
            for i, t in enumerate(tracks)
        ]
    }


async def fix_cold_visions_tracks():
    """Исправить треки Cold Visions"""
    
    print("=" * 80)
    print("ИСПРАВЛЕНИЕ ТРЕКОВ COLD VISIONS")
    print("=" * 80)
    
    # Получить информацию об альбоме
    album_info = await get_lastfm_album_info("Bladee", "Cold Visions")
    
    if not album_info:
        print("Не удалось получить информацию об альбоме")
        return
    
    print(f"\nАльбом: {album_info['name']} by {album_info['artist']}")
    print(f"Обложка: {album_info['cover_url'][:50]}..." if album_info['cover_url'] else "Обложка: нет")
    print(f"Треков: {len(album_info['tracks'])}")
    
    # Нормализованные названия треков для сопоставления
    lastfm_tracks = {
        normalize_title(t['name']): t
        for t in album_info['tracks']
    }
    
    async with get_session() as session:
        # Найти альбом в базе
        result = await session.execute(
            select(Album).where(Album.name == "Cold Visions")
        )
        album = result.scalar_one_or_none()
        
        if not album:
            print("Альбом Cold Visions не найден в базе!")
            return
        
        print(f"\nАльбом ID: {album.id}")
        
        # Обновить обложку альбома если нет
        if not album.cover_url and album_info['cover_url']:
            album.cover_url = album_info['cover_url']
            print("Обновлена обложка альбома")
        
        # Получить все треки Bladee
        result = await session.execute(
            select(Track)
            .options(selectinload(Track.enrichment))
            .where(Track.artist.ilike("%bladee%"))
        )
        all_bladee = result.scalars().all()
        
        # Создать словарь для быстрого поиска
        bladee_by_norm = {}
        for t in all_bladee:
            norm = normalize_title(t.title)
            if norm not in bladee_by_norm:
                bladee_by_norm[norm] = []
            bladee_by_norm[norm].append(t)
        
        fixed_count = 0
        added_to_album_count = 0
        
        for lastfm_norm, lastfm_track in lastfm_tracks.items():
            # Найти соответствующий трек в библиотеке
            matching_tracks = bladee_by_norm.get(lastfm_norm, [])
            
            # Если не найден точно, попробовать fuzzy matching
            if not matching_tracks:
                for norm, tracks in bladee_by_norm.items():
                    if fuzzy_match_title(lastfm_norm, norm) >= 0.8:
                        matching_tracks = tracks
                        break
            
            if not matching_tracks:
                print(f"  ✗ НЕ НАЙДЕН: {lastfm_track['name']}")
                continue
            
            for track in matching_tracks:
                needs_fix = False
                
                # Проверить enrichment
                if track.enrichment:
                    if track.enrichment.album_name != "Cold Visions":
                        old_album = track.enrichment.album_name
                        track.enrichment.album_name = "Cold Visions"
                        track.enrichment.track_number = lastfm_track['number']
                        
                        if album_info['cover_url'] and not track.enrichment.cover_url:
                            track.enrichment.cover_url = album_info['cover_url']
                        
                        print(f"  ✓ ИСПРАВЛЕН: [{track.id}] {track.title}")
                        print(f"      album: {old_album or 'None'} -> Cold Visions")
                        needs_fix = True
                        fixed_count += 1
                else:
                    # Создать enrichment
                    track.enrichment = TrackEnrichment(
                        track_id=track.id,
                        album_name="Cold Visions",
                        cover_url=album_info['cover_url'],
                        track_number=lastfm_track['number'],
                    )
                    session.add(track.enrichment)
                    print(f"  ✓ СОЗДАН ENRICHMENT: [{track.id}] {track.title}")
                    needs_fix = True
                    fixed_count += 1
                
                # Проверить, есть ли трек в album_tracks
                result = await session.execute(
                    select(AlbumTrack).where(
                        AlbumTrack.album_id == album.id,
                        AlbumTrack.track_id == track.id
                    )
                )
                album_track = result.scalar_one_or_none()
                
                if not album_track:
                    # Добавить в альбом
                    new_at = AlbumTrack(
                        album_id=album.id,
                        track_id=track.id,
                        track_number=lastfm_track['number']
                    )
                    session.add(new_at)
                    print(f"      + добавлен в album_tracks (track #{lastfm_track['number']})")
                    added_to_album_count += 1
                elif album_track.track_number != lastfm_track['number']:
                    # Обновить номер трека
                    album_track.track_number = lastfm_track['number']
                    print(f"      ~ обновлён track_number: {lastfm_track['number']}")
        
        await session.commit()
        
        print(f"\n{'=' * 80}")
        print(f"ИТОГО:")
        print(f"  Исправлено enrichment: {fixed_count}")
        print(f"  Добавлено в album_tracks: {added_to_album_count}")
        print(f"{'=' * 80}")


if __name__ == "__main__":
    asyncio.run(fix_cold_visions_tracks())

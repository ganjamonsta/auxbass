#!/usr/bin/env python3
"""
Переобогащение треков без альбома через tracklist_matcher

Этот скрипт:
1. Находит все треки со статусом COMPLETED но без album_name
2. Пытается найти альбом через поиск в треклистах (tracklist_matcher)
3. Обновляет enrichment с найденным альбомом

Особенно полезно для:
- Треков с (feat. X) которые не находятся напрямую
- Треков с нестандартным написанием
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from shared.database import get_session
from shared.models import Track, TrackEnrichment, EnrichmentStatus
from bot.services.enrichment.tracklist_matcher import album_tracklist_matcher

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def re_enrich_tracks_without_album(
    artist_filter: str = None,
    limit: int = 100,
    dry_run: bool = False
):
    """
    Переобогатить треки без альбома
    
    Args:
        artist_filter: Фильтр по артисту (опционально)
        limit: Максимальное количество треков для обработки
        dry_run: Если True, только показать что будет сделано
    """
    
    print("=" * 80)
    print("ПЕРЕОБОГАЩЕНИЕ ТРЕКОВ БЕЗ АЛЬБОМА")
    print("=" * 80)
    
    if dry_run:
        print(">>> РЕЖИМ СИМУЛЯЦИИ (dry_run=True) <<<\n")
    
    async with get_session() as session:
        # Найти треки COMPLETED без album_name
        query = (
            select(Track)
            .options(selectinload(Track.enrichment))
            .join(TrackEnrichment, TrackEnrichment.track_id == Track.id)
            .where(
                Track.enrichment_status == EnrichmentStatus.COMPLETED,
                TrackEnrichment.album_name.is_(None)
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
        
        # Группировать по артисту для эффективности
        by_artist = {}
        for track in tracks:
            artist = track.artist or "Unknown"
            if artist not in by_artist:
                by_artist[artist] = []
            by_artist[artist].append(track)
        
        print(f"Артистов для обработки: {len(by_artist)}")
        
        found_count = 0
        processed_count = 0
        
        for artist, artist_tracks in by_artist.items():
            print(f"\n--- Артист: {artist} ({len(artist_tracks)} треков) ---")
            
            for track in artist_tracks:
                processed_count += 1
                
                # Попытка найти альбом через треклист
                match = await album_tracklist_matcher.find_album_for_track(
                    track_title=track.title,
                    artist=artist,
                    match_threshold=0.75
                )
                
                if match:
                    found_count += 1
                    album_name = match.get("album_name")
                    cover_url = match.get("cover_url")
                    track_number = match.get("track_number")
                    
                    print(f"  + [{track.id}] {track.title}")
                    print(f"      -> альбом: {album_name} (track #{track_number})")
                    
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
                else:
                    print(f"  - [{track.id}] {track.title} - не найден в треклистах")
        
        if not dry_run:
            await session.commit()
        
        print(f"\n{'=' * 80}")
        print(f"ИТОГО:")
        print(f"  Обработано: {processed_count}")
        print(f"  Найдено альбомов: {found_count}")
        if dry_run:
            print(f"  (режим симуляции - изменения НЕ сохранены)")
        else:
            print(f"  Изменения сохранены в базе данных")
        print(f"{'=' * 80}")
    
    # Закрыть клиент
    await album_tracklist_matcher.close()


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Переобогащение треков без альбома')
    parser.add_argument('--artist', '-a', type=str, help='Фильтр по артисту')
    parser.add_argument('--limit', '-l', type=int, default=100, help='Лимит треков')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Режим симуляции')
    
    args = parser.parse_args()
    
    await re_enrich_tracks_without_album(
        artist_filter=args.artist,
        limit=args.limit,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    asyncio.run(main())

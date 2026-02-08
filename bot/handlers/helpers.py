"""
TG Player Bot - Shared Handler Helpers

Common functions used by both commands.py and callbacks.py
to avoid code duplication.
"""
from typing import List, Dict, Optional, Union
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from shared.database import get_session
from shared.models import Playlist
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bot.services import track_service


async def get_playlist_list_data(user_id: int) -> List[Dict]:
    """
    Fetch playlist data for a user.
    Returns list of dicts with id, name, track_count.
    """
    async with get_session() as session:
        result = await session.execute(
            select(Playlist)
            .options(selectinload(Playlist.tracks))
            .where(Playlist.owner_id == user_id)
            .order_by(Playlist.created_at.desc())
        )
        playlists = result.scalars().all()
        
        playlist_data = []
        for pl in playlists[:20]:
            track_count = len(pl.tracks) if pl.tracks else 0
            playlist_data.append({
                'id': pl.id,
                'name': pl.name,
                'track_count': track_count
            })
    
    return playlist_data


def format_playlist_list(playlist_data: List[Dict]) -> tuple:
    """
    Format playlist list text and keyboard.
    Returns (text, keyboard_markup) or (empty_text, None) if no playlists.
    """
    if not playlist_data:
        text = (
            "📁 <b>Мои плейлисты</b>\n\n"
            "У тебя пока нет плейлистов.\n\n"
            "<b>Как создать?</b>\n"
            "• /playlist — интерактивное создание\n"
            '• /playlist "Название" — быстрое создание'
        )
        return text, None
    
    text = "📁 <b>Мои плейлисты</b>\n\n"
    keyboard = []
    
    for pl in playlist_data:
        text += f"• <b>{pl['name']}</b> — {pl['track_count']} 🎵\n"
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"📁 {pl['name']}",
                callback_data=f"pl:menu:{pl['id']}"
            )
        ])
    
    text += "\n<b>Управление:</b> нажми на плейлист"
    
    return text, InlineKeyboardMarkup(inline_keyboard=keyboard)


async def format_stats_text(user_id: int) -> str:
    """
    Format library statistics text.
    Returns formatted HTML string.
    """
    stats = await track_service.get_library_stats(user_id)
    
    total_seconds = stats.get("total_duration_seconds", 0)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    enrichment = stats.get("enrichment", {})
    pending = enrichment.get("pending", 0)
    failed = enrichment.get("failed", 0)
    
    enrichment_text = ""
    if pending > 0:
        enrichment_text = f"\n🔄 Обогащение: {pending} в очереди"
    elif failed > 0:
        enrichment_text = f"\n⚠️ Не обогащено: {failed} треков"
    
    return (
        "📊 <b>Статистика библиотеки</b>\n\n"
        f"🎵 Треков: <b>{stats['total_tracks']}</b>\n"
        f"💿 Альбомов: <b>{stats['album_count']}</b>\n"
        f"⏱ Общая длительность: <b>{hours}ч {minutes}мин</b>{enrichment_text}"
    )

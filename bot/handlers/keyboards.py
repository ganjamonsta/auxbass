"""
TG Player Bot - Keyboard Utilities v2

Reusable keyboard builders for consistent UI.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from typing import List, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.config import get_settings
from shared.models import Track

settings = get_settings()


def get_webapp_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with Mini App button"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎵 Открыть плеер",
            web_app=WebAppInfo(url=settings.webapp_url)
        )]
    ])


def get_help_menu_keyboard() -> InlineKeyboardMarkup:
    """Create main help menu with section buttons"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Добавление музыки", callback_data="help:upload")],
        [InlineKeyboardButton(text="📁 Плейлисты", callback_data="help:playlists")],
        [InlineKeyboardButton(text="💿 Альбомы и исполнители", callback_data="help:albums")],
        [InlineKeyboardButton(text="☁️ Облачный бекап", callback_data="help:backup")],
        [InlineKeyboardButton(text="🎧 Веб-плеер", callback_data="help:player")],
        [InlineKeyboardButton(text="📱 Все команды", callback_data="help:commands")],
        [InlineKeyboardButton(
            text="🎵 Открыть плеер",
            web_app=WebAppInfo(url=settings.webapp_url)
        )]
    ])


def get_help_back_keyboard() -> InlineKeyboardMarkup:
    """Create back button for help sections"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад к меню", callback_data="help:menu")],
        [InlineKeyboardButton(
            text="🎵 Открыть плеер",
            web_app=WebAppInfo(url=settings.webapp_url)
        )]
    ])


def get_help_player_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for web player help with site link"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад к меню", callback_data="help:menu")],
        [InlineKeyboardButton(
            text="🎵 Открыть плеер",
            web_app=WebAppInfo(url=settings.webapp_url)
        )],
        [InlineKeyboardButton(
            text="🌐 Открыть сайт",
            url="https://aux.ganjacraft.ru"
        )]
    ])


def get_track_keyboard(track_id: int, show_enrich: bool = False) -> InlineKeyboardMarkup:
    """
    Create keyboard for track message.
    
    Args:
        track_id: Track ID
        show_enrich: Show re-enrich button
    """
    buttons = [
        [InlineKeyboardButton(
            text="🎵 Открыть плеер",
            web_app=WebAppInfo(url=settings.webapp_url)
        )],
        [InlineKeyboardButton(
            text="📥 Скачать",
            callback_data=f"download_track:{track_id}"
        )],
    ]
    
    if show_enrich:
        buttons.append([
            InlineKeyboardButton(
                text="🔄 Обновить метаданные",
                callback_data=f"enrich_track:{track_id}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(
            text="❌ Удалить из библиотеки",
            callback_data=f"delete_track:{track_id}"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_playlist_mode_keyboard(track_count: int) -> InlineKeyboardMarkup:
    """Create keyboard for playlist creation mode"""
    finish_text = f"✓ Завершить ({track_count} треков)" if track_count > 0 else "✓ Завершить"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=finish_text, callback_data="playlist:finish"),
            InlineKeyboardButton(text="✗ Отменить", callback_data="playlist:cancel")
        ]
    ])


def get_duplicate_keyboard(existing_track_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for duplicate track confirmation"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✓ Добавить в плейлист",
                callback_data=f"playlist:add_existing:{existing_track_id}"
            ),
            InlineKeyboardButton(
                text="✗ Пропустить",
                callback_data="playlist:skip_duplicate"
            )
        ]
    ])


def get_album_keyboard(album_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for album"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎵 Слушать альбом",
            web_app=WebAppInfo(url=f"{settings.webapp_url}?album={album_id}")
        )],
        [InlineKeyboardButton(
            text="📋 Показать треки",
            callback_data=f"album_tracks:{album_id}"
        )],
    ])


def get_channel_setup_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for channel setup instructions"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Канал создан, проверить",
            callback_data="channel:verify"
        )],
        [InlineKeyboardButton(
            text="❓ Помощь",
            callback_data="channel:help"
        )],
    ])


def get_channel_keyboard(channel_id: int, channel_username: Optional[str] = None) -> InlineKeyboardMarkup:
    """Create keyboard for user's backup channel"""
    buttons = []
    
    if channel_username:
        buttons.append([
            InlineKeyboardButton(
                text="📢 Открыть канал",
                url=f"https://t.me/{channel_username}"
            )
        ])
    
    buttons.extend([
        [InlineKeyboardButton(
            text="⚙️ Настройки канала",
            callback_data="channel:settings"
        )],
        [InlineKeyboardButton(
            text="🔄 Синхронизировать",
            callback_data="channel:sync"
        )],
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_pagination_keyboard(
    callback_prefix: str,
    current_page: int,
    total_pages: int,
    extra_buttons: Optional[List[InlineKeyboardButton]] = None,
) -> InlineKeyboardMarkup:
    """
    Create pagination keyboard.
    
    Args:
        callback_prefix: Prefix for callback data (e.g., "tracks")
        current_page: Current page (0-indexed)
        total_pages: Total number of pages
        extra_buttons: Additional buttons to add after pagination
    """
    buttons = []
    nav_row = []
    
    if current_page > 0:
        nav_row.append(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"{callback_prefix}:page:{current_page - 1}"
        ))
    
    # Page indicator
    nav_row.append(InlineKeyboardButton(
        text=f"{current_page + 1}/{total_pages}",
        callback_data="noop"
    ))
    
    if current_page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(
            text="Вперёд ▶️",
            callback_data=f"{callback_prefix}:page:{current_page + 1}"
        ))
    
    if nav_row:
        buttons.append(nav_row)
    
    if extra_buttons:
        buttons.append(extra_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_stats_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for stats command"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎵 Открыть плеер",
            web_app=WebAppInfo(url=settings.webapp_url)
        )],
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="stats:refresh"),
            InlineKeyboardButton(text="🔍 Дубликаты", callback_data="stats:dedup"),
        ]
    ])


def get_confirm_keyboard(confirm_callback: str, cancel_callback: str = "cancel") -> InlineKeyboardMarkup:
    """Create confirmation keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=confirm_callback),
            InlineKeyboardButton(text="❌ Отмена", callback_data=cancel_callback),
        ]
    ])


def get_cancel_keyboard(callback_data: str = "cancel") -> InlineKeyboardMarkup:
    """Simple cancel button"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✗ Отменить", callback_data=callback_data)]
    ])


def get_deduplication_action_keyboard(tracks: List[Track], current_index: int, total_groups: int, confirm_delete_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """
    Keyboard for duplicate resolution.
    Allows playing specific tracks and deleting individual duplicates.
    User can delete tracks one by one or skip to keep all.
    
    Args:
        tracks: List of duplicate tracks
        current_index: Current group index
        total_groups: Total number of duplicate groups
        confirm_delete_id: If set, show confirmation for this track ID
    """
    buttons = []
    
    # Each track gets its own row with Play and Delete buttons
    for idx, track in enumerate(tracks):
        if confirm_delete_id == track.id:
            # Show confirmation buttons for this track
            buttons.append([
                InlineKeyboardButton(text=f"✅ Да, удалить #{idx+1}", callback_data=f"dedup:confirm_delete:{track.id}"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="dedup:cancel_delete"),
            ])
        else:
            # Normal row: Play + Delete
            buttons.append([
                InlineKeyboardButton(text=f"▶️ #{idx+1}", callback_data=f"dedup:play:{track.id}"),
                InlineKeyboardButton(text=f"🗑 Удалить #{idx+1}", callback_data=f"dedup:delete:{track.id}"),
            ])
            
    # Navigation and actions - all on one row
    buttons.append([
        InlineKeyboardButton(text="➡️ Далее", callback_data="dedup:next"),
        InlineKeyboardButton(text=f"📊 {current_index+1}/{total_groups}", callback_data="dedup:noop"),
        InlineKeyboardButton(text="❌ Выход", callback_data="dedup:cancel"),
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


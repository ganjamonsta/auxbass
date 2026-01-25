"""
TG Player Bot - Keyboard Utilities
Reusable keyboard builders for consistent UI
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.config import get_settings

settings = get_settings()


def get_webapp_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with Mini App button"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎵 Открыть плеер",
            web_app=WebAppInfo(url=settings.webapp_url)
        )]
    ])


def get_track_keyboard(track_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for track message"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎵 Открыть плеер",
            web_app=WebAppInfo(url=settings.webapp_url)
        )],
        [InlineKeyboardButton(
            text="📥 Скачать",
            callback_data=f"download_track:{track_id}"
        )],
        [InlineKeyboardButton(
            text="❌ Удалить из библиотеки",
            callback_data=f"delete_track:{track_id}"
        )]
    ])


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


def get_playlist_list_keyboard(playlists: list, page: int = 0, page_size: int = 5) -> InlineKeyboardMarkup:
    """Create paginated playlist list keyboard"""
    start = page * page_size
    end = start + page_size
    page_playlists = playlists[start:end]
    
    buttons = []
    
    # Playlist buttons
    for pl in page_playlists:
        buttons.append([
            InlineKeyboardButton(
                text=f"📁 {pl.name} ({len(pl.tracks) if hasattr(pl, 'tracks') else '?'} треков)",
                callback_data=f"pl_open:{pl.id}"
            )
        ])
    
    # Pagination
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="◀️", callback_data=f"pl_page:{page-1}"))
    if end < len(playlists):
        nav_row.append(InlineKeyboardButton(text="▶️", callback_data=f"pl_page:{page+1}"))
    
    if nav_row:
        buttons.append(nav_row)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cancel_keyboard(callback_data: str = "cancel") -> InlineKeyboardMarkup:
    """Simple cancel button"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✗ Отменить", callback_data=callback_data)]
    ])

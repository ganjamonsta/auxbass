"""
TG Player Bot - Hierarchical Menu Keyboards

All keyboard builders for the unified menu system.
Callback data convention:
    menu:<section>          — navigation between top-level sections
    lib:<action>            — library actions
    pl:<action>[:<id>]      — playlist actions
    ch:<action>             — channel actions
    stats:<action>          — statistics actions
"""
from typing import Optional, List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from shared.config import get_settings

settings = get_settings()


# ──────────────────────── Main Menu ────────────────────────

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu — 4 top-level sections"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Моя библиотека", callback_data="menu:library")],
        [InlineKeyboardButton(text="🗂 Плейлисты", callback_data="menu:playlists")],
        [InlineKeyboardButton(text="☁️ Мой канал", callback_data="menu:channel")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="menu:stats")],
    ])


# ──────────────────────── Library ────────────────────────

def get_library_keyboard(track_count: int) -> InlineKeyboardMarkup:
    """Library section keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎵 Открыть плеер",
            web_app=WebAppInfo(url=settings.webapp_url),
        )],
        [InlineKeyboardButton(text="🗂 Плейлисты", callback_data="menu:playlists")],
        [InlineKeyboardButton(
            text="🌐 Войти из браузера",
            callback_data="lib:login",
        )],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main")],
    ])


# ──────────────────────── Playlists ────────────────────────

def get_playlists_keyboard(
    playlists: List[dict],
) -> InlineKeyboardMarkup:
    """
    Playlists list keyboard.
    Each playlist is a dict with 'id', 'name', 'track_count'.
    """
    buttons = []
    for pl in playlists:
        buttons.append([
            InlineKeyboardButton(
                text=f"📁 {pl['name']} ({pl['track_count']} 🎵)",
                callback_data=f"pl:menu:{pl['id']}",
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="➕ Создать плейлист", callback_data="pl:create"),
    ])
    buttons.append([
        InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_playlists_empty_keyboard() -> InlineKeyboardMarkup:
    """Playlists section when user has none"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать плейлист", callback_data="pl:create")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main")],
    ])


def get_playlist_detail_keyboard(playlist_id: int) -> InlineKeyboardMarkup:
    """Single playlist management"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎵 Слушать",
            web_app=WebAppInfo(url=f"{settings.webapp_url}?playlist={playlist_id}"),
        )],
        [InlineKeyboardButton(
            text="📥 Скачать все треки",
            callback_data=f"download_playlist:{playlist_id}",
        )],
        [
            InlineKeyboardButton(text="✏️ Переименовать", callback_data=f"pl:rename:{playlist_id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"pl:delete_confirm:{playlist_id}"),
        ],
        [InlineKeyboardButton(text="◀️ Плейлисты", callback_data="menu:playlists")],
    ])


def get_playlist_delete_confirm_keyboard(playlist_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗑 Да, удалить", callback_data=f"pl:delete:{playlist_id}"),
            InlineKeyboardButton(text="✗ Отмена", callback_data=f"pl:menu:{playlist_id}"),
        ]
    ])


def get_playlist_create_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✗ Отмена", callback_data="pl:cancel_input")],
    ])


def get_playlist_building_keyboard(track_count: int) -> InlineKeyboardMarkup:
    """Keyboard shown while user is adding tracks to a playlist"""
    finish_text = f"✓ Завершить ({track_count} треков)" if track_count else "✓ Завершить"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=finish_text, callback_data="playlist:finish"),
            InlineKeyboardButton(text="✗ Отменить", callback_data="playlist:cancel"),
        ]
    ])


# ──────────────────────── Channel ────────────────────────

def get_channel_not_connected_keyboard() -> InlineKeyboardMarkup:
    """Channel section when no channel is connected"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Подключить канал", callback_data="ch:setup")],
        [InlineKeyboardButton(text="❓ Как это работает?", callback_data="ch:help")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main")],
    ])


def get_channel_main_keyboard(
    channel_username: Optional[str] = None,
) -> InlineKeyboardMarkup:
    """Channel section — main dashboard"""
    buttons = []

    if channel_username:
        buttons.append([
            InlineKeyboardButton(
                text="📢 Открыть канал",
                url=f"https://t.me/{channel_username}",
            )
        ])

    buttons.extend([
        [InlineKeyboardButton(text="🔍 Проверить канал", callback_data="ch:scan")],
        [InlineKeyboardButton(text="📤 Восстановить отсутствующие", callback_data="ch:restore")],
        [InlineKeyboardButton(text="🔎 Найти дубликаты", callback_data="ch:duplicates")],
        [InlineKeyboardButton(text="🔄 Пересканировать канал", callback_data="ch:reset_confirm")],
        [InlineKeyboardButton(text="⚙️ Настройки канала", callback_data="ch:settings")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main")],
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_channel_settings_keyboard() -> InlineKeyboardMarkup:
    """Channel settings sub-menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отключить канал", callback_data="ch:disconnect_confirm")],
        [InlineKeyboardButton(text="◀️ Мой канал", callback_data="menu:channel")],
    ])


def get_channel_disconnect_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❌ Да, отключить", callback_data="ch:disconnect"),
            InlineKeyboardButton(text="✗ Отмена", callback_data="ch:settings"),
        ]
    ])


def get_channel_setup_waiting_keyboard() -> InlineKeyboardMarkup:
    """Waiting for user to forward a message from channel"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✗ Отмена", callback_data="ch:setup_cancel")],
    ])


def get_channel_reset_confirm_keyboard() -> InlineKeyboardMarkup:
    """Confirm clearing ChannelMessage and rescanning"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Да, пересканировать", callback_data="ch:reset"),
            InlineKeyboardButton(text="✗ Отмена", callback_data="menu:channel"),
        ]
    ])


def get_channel_operation_keyboard(cancel_callback: str = "ch:op_cancel") -> InlineKeyboardMarkup:
    """Generic cancel button for long channel operations"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⛔ Прервать", callback_data=cancel_callback)],
    ])


def get_channel_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Мой канал", callback_data="menu:channel")],
    ])


# ──────────────────────── Statistics ────────────────────────

def get_stats_menu_keyboard() -> InlineKeyboardMarkup:
    """Statistics section keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="stats:refresh")],
        [InlineKeyboardButton(
            text="🎵 Открыть плеер",
            web_app=WebAppInfo(url=settings.webapp_url),
        )],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main")],
    ])

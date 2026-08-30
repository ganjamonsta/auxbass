"""
TG Player Bot - Clean Modern Menu Keyboards

Callback data convention:
    menu:<section>          — navigation between top-level sections
    lib:<action>            — library actions
    ch:<action>             — channel actions
    stats:<action>          — statistics actions
"""
from typing import Optional, List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from shared.config import get_settings

settings = get_settings()


# ──────────────────────── Main Menu ────────────────────────

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu — sleek and minimal with prominent WebApp button"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎵 Открыть плеер",
            web_app=WebAppInfo(url=settings.webapp_url),
        )],
        [
            InlineKeyboardButton(text="☁️ Мой канал", callback_data="menu:channel"),
            InlineKeyboardButton(text="🌐 Вход в браузере", callback_data="lib:login"),
        ],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="menu:stats"),
        ],
    ])


def get_webapp_keyboard() -> InlineKeyboardMarkup:
    """Single WebApp player launch button"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎵 Открыть плеер",
            web_app=WebAppInfo(url=settings.webapp_url),
        )]
    ])


def get_track_keyboard(track_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Keyboard for single track confirmation"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎵 Открыть плеер",
            web_app=WebAppInfo(url=settings.webapp_url),
        )]
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
    """Channel section — clean dashboard"""
    buttons = []

    if channel_username:
        buttons.append([
            InlineKeyboardButton(
                text="📢 Открыть канал",
                url=f"https://t.me/{channel_username}",
            )
        ])

    buttons.extend([
        [InlineKeyboardButton(text="📥 Импорт из result.json", callback_data="ch:import_help")],
        [InlineKeyboardButton(text="📤 Загрузить недостающие в канал", callback_data="ch:restore")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="ch:settings")],
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


def get_channel_operation_keyboard(cancel_callback: str = "ch:op_cancel") -> InlineKeyboardMarkup:
    """Cancel button for long channel operations"""
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
        [InlineKeyboardButton(
            text="🎵 Открыть плеер",
            web_app=WebAppInfo(url=settings.webapp_url),
        )],
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="stats:refresh"),
            InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main"),
        ],
    ])

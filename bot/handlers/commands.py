"""
TG Player Bot - Command Handlers
"""
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from sqlalchemy import select, func

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.config import get_settings
from shared.database import get_session
from shared.models import User, Track, Playlist


router = Router()
settings = get_settings()


def get_webapp_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with Mini App button"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎵 Открыть плеер",
            web_app=WebAppInfo(url=settings.webapp_url)
        )]
    ])


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command"""
    user = message.from_user
    
    async with get_session() as session:
        # Get or create user
        db_user = await session.get(User, user.id)
        
        if not db_user:
            db_user = User(
                id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )
            session.add(db_user)
        else:
            # Update user info
            db_user.username = user.username
            db_user.first_name = user.first_name
            db_user.last_name = user.last_name
    
    await message.answer(
        f"👋 Привет, <b>{user.first_name}</b>!\n\n"
        "🎵 <b>TG Player</b> — твоя музыкальная библиотека в Telegram.\n\n"
        "📤 <b>Отправь мне аудиофайл</b> — я добавлю его в твою библиотеку.\n\n"
        "📂 Нажми кнопку ниже, чтобы открыть плеер:",
        reply_markup=get_webapp_keyboard()
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    await message.answer(
        "🎵 <b>TG Player — Справка</b>\n\n"
        "<b>Как добавить музыку?</b>\n"
        "Просто отправь мне аудиофайл (MP3, FLAC, и др.) — "
        "я автоматически добавлю его в твою библиотеку.\n\n"
        "<b>Команды:</b>\n"
        "/start — Начало работы\n"
        "/help — Эта справка\n"
        "/library — Открыть плеер\n"
        "/stats — Статистика библиотеки\n\n"
        "<b>Возможности плеера:</b>\n"
        "• Создание плейлистов\n"
        "• Поиск по артисту, названию, жанру\n"
        "• Редактирование метаданных\n"
        "• Управление воспроизведением",
        reply_markup=get_webapp_keyboard()
    )


@router.message(Command("library"))
async def cmd_library(message: Message):
    """Handle /library command - open Mini App"""
    await message.answer(
        "🎵 Нажми кнопку, чтобы открыть плеер:",
        reply_markup=get_webapp_keyboard()
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Handle /stats command"""
    user_id = message.from_user.id
    
    async with get_session() as session:
        # Count tracks
        tracks_count = await session.scalar(
            select(func.count(Track.id)).where(Track.user_id == user_id)
        )
        
        # Count playlists
        playlists_count = await session.scalar(
            select(func.count(Playlist.id)).where(Playlist.user_id == user_id)
        )
        
        # Total duration
        total_duration = await session.scalar(
            select(func.sum(Track.duration)).where(Track.user_id == user_id)
        ) or 0
        
        # Format duration
        hours = total_duration // 3600
        minutes = (total_duration % 3600) // 60
    
    await message.answer(
        "📊 <b>Статистика библиотеки</b>\n\n"
        f"🎵 Треков: <b>{tracks_count or 0}</b>\n"
        f"📁 Плейлистов: <b>{playlists_count or 0}</b>\n"
        f"⏱ Общая длительность: <b>{hours}ч {minutes}мин</b>",
        reply_markup=get_webapp_keyboard()
    )

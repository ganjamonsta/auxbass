"""
TG Player Bot - Audio Handler
"""
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.config import get_settings
from shared.database import get_session
from shared.models import User, Track


router = Router()
settings = get_settings()


def get_track_keyboard(track_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for track message"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎵 Открыть плеер",
            web_app=WebAppInfo(url=settings.webapp_url)
        )],
        [InlineKeyboardButton(
            text="❌ Удалить из библиотеки",
            callback_data=f"delete_track:{track_id}"
        )]
    ])


def format_duration(seconds: int | None) -> str:
    """Format duration in seconds to MM:SS"""
    if not seconds:
        return "—"
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


@router.message(F.audio)
async def handle_audio(message: Message):
    """Handle incoming audio files"""
    audio = message.audio
    user = message.from_user
    
    async with get_session() as session:
        # Ensure user exists
        db_user = await session.get(User, user.id)
        if not db_user:
            db_user = User(
                id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )
            session.add(db_user)
            await session.flush()
        
        # Check if track already exists
        existing = await session.scalar(
            select(Track).where(
                Track.user_id == user.id,
                Track.file_unique_id == audio.file_unique_id
            )
        )
        
        if existing:
            await message.reply(
                "⚠️ Этот трек уже есть в твоей библиотеке!\n\n"
                f"🎵 <b>{existing.title or 'Без названия'}</b>\n"
                f"👤 {existing.artist or 'Неизвестный исполнитель'}",
                reply_markup=get_track_keyboard(existing.id)
            )
            return
        
        # Create new track
        track = Track(
            user_id=user.id,
            file_id=audio.file_id,
            file_unique_id=audio.file_unique_id,
            title=audio.title,
            artist=audio.performer,
            duration=audio.duration,
            file_size=audio.file_size,
            mime_type=audio.mime_type,
        )
        
        session.add(track)
        
        try:
            await session.flush()
            track_id = track.id
        except IntegrityError:
            await message.reply("⚠️ Этот трек уже добавлен!")
            return
    
    # Build response
    title = audio.title or "Без названия"
    artist = audio.performer or "Неизвестный исполнитель"
    duration = format_duration(audio.duration)
    size_mb = (audio.file_size or 0) / (1024 * 1024)
    
    await message.reply(
        f"✅ <b>Трек добавлен в библиотеку!</b>\n\n"
        f"🎵 <b>{title}</b>\n"
        f"👤 {artist}\n"
        f"⏱ {duration} • {size_mb:.1f} MB",
        reply_markup=get_track_keyboard(track_id)
    )


@router.message(F.voice)
async def handle_voice(message: Message):
    """Handle voice messages - inform user"""
    await message.reply(
        "🎤 Голосовые сообщения не поддерживаются.\n"
        "Отправь аудиофайл (MP3, FLAC и др.)"
    )


@router.message(F.document)
async def handle_document(message: Message):
    """Handle documents - check if audio"""
    doc = message.document
    
    if doc.mime_type and doc.mime_type.startswith("audio/"):
        await message.reply(
            "💡 Отправь этот файл как <b>аудио</b>, а не как документ.\n\n"
            "Для этого при отправке выбери 'Отправить как музыку' или "
            "используй скрепку → Музыка."
        )
    # Ignore non-audio documents

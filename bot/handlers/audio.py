"""
TG Player Bot - Audio Handler v2

Handles audio file uploads and forwards.
Uses new modular service architecture.
"""
from aiogram import Router, F
from aiogram.types import Message
from typing import Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.config import get_settings
from shared.database import get_session
from shared.models import User, Track, LibrarySource, ForwardSourceType, UserChannel
from shared.utils import format_duration

from bot.services import track_service, channel_service
from bot.services.session import session_manager
from bot.handlers.keyboards import (
    get_track_keyboard,
    get_playlist_mode_keyboard,
    get_duplicate_keyboard,
)


router = Router()
settings = get_settings()


def extract_forward_info(message: Message) -> dict:
    """
    Extract forward source information from a message.
    
    Returns:
        Dict with source_type, source_id, source_name
    """
    info = {
        "source_type": None,
        "source_id": None,
        "source_name": None,
    }
    
    # Check for forwarded from user/bot
    if message.forward_from:
        user = message.forward_from
        info["source_type"] = ForwardSourceType.BOT if user.is_bot else ForwardSourceType.USER
        info["source_id"] = user.id
        info["source_name"] = (
            f"{user.first_name or ''} {user.last_name or ''}".strip() 
            or user.username 
            or str(user.id)
        )
    
    # Check for forwarded from channel/chat
    elif message.forward_from_chat:
        chat = message.forward_from_chat
        if chat.type == "channel":
            info["source_type"] = ForwardSourceType.CHANNEL
        else:
            info["source_type"] = ForwardSourceType.CHAT
        info["source_id"] = chat.id
        info["source_name"] = chat.title or chat.username or str(chat.id)
    
    # Hidden forward (privacy settings)
    elif message.forward_sender_name:
        info["source_type"] = ForwardSourceType.HIDDEN
        info["source_name"] = message.forward_sender_name
    
    return info


def get_library_source(message: Message) -> LibrarySource:
    """Determine library source from message"""
    if message.forward_from or message.forward_from_chat or message.forward_sender_name:
        return LibrarySource.SHARED
    return LibrarySource.UPLOADED


@router.message(F.audio)
async def handle_audio(message: Message):
    """
    Handle incoming audio files.
    
    Flow:
    1. Check if user has connected channel (required for saving)
    2. Save track using track_service (handles deduplication)
    3. If new track: schedule enrichment
    4. If user has channel: forward to channel
    5. Show result to user
    """
    audio = message.audio
    user = message.from_user
    user_id = user.id
    
    # Check if user has connected channel (required to save tracks)
    async with get_session() as session:
        from sqlalchemy import select
        channel = await session.scalar(
            select(UserChannel).where(
                UserChannel.user_id == user_id,
                UserChannel.is_active == True
            )
        )
        
        if not channel:
            await message.reply(
                "🔒 <b>Подключите канал для сохранения музыки</b>\n\n"
                "Чтобы загружать треки и пользоваться библиотекой, "
                "нужно подключить ваш Telegram-канал.\n\n"
                "Используйте команду /channel для подключения.\n\n"
                "<i>После подключения вы сможете:</i>\n"
                "• 📁 Загружать треки в библиотеку\n"
                "• ❤️ Лайкать и сохранять музыку\n"
                "• 📋 Создавать плейлисты\n"
                "• ☁️ Автоматический бэкап в канал",
                parse_mode="HTML"
            )
            return
    
    # Extract metadata
    title = audio.title or "Без названия"
    artist = audio.performer
    duration = audio.duration
    file_size = audio.file_size
    
    # Extract forward info
    forward_info = extract_forward_info(message)
    library_source = get_library_source(message)
    
    # Check if in playlist creation mode
    playlist_session = session_manager.get_playlist_session(user_id)
    
    async with get_session() as session:
        # Ensure user exists
        db_user = await session.get(User, user_id)
        if not db_user:
            db_user = User(
                id=user_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )
            session.add(db_user)
            await session.flush()
    
    # Save track using service
    result = await track_service.save_track(
        user_id=user_id,
        file_id=audio.file_id,
        file_unique_id=audio.file_unique_id,
        title=title,
        artist=artist,
        duration=duration,
        file_size=file_size,
        library_source=library_source,
        forward_source_type=forward_info["source_type"],
        forward_source_id=forward_info["source_id"],
        forward_source_name=forward_info["source_name"],
        enrich=True,  # Auto-schedule enrichment
    )
    
    track_id = result.track_id
    is_new = result.is_new
    
    # If user has backup channel, queue track for forwarding
    channel_queued = False
    try:
        channel_queued = await channel_service.forward_track_to_channel(
            user_id=user_id,
            track_id=track_id,
            bot=message.bot,
        )
    except Exception as e:
        # Channel forwarding is optional, don't fail the main operation
        pass
    
    # Build response
    duration_str = format_duration(duration) if duration else ""
    size_mb = (file_size or 0) / (1024 * 1024)
    
    # Source info
    source_note = ""
    if forward_info["source_type"] and forward_info["source_type"] != ForwardSourceType.HIDDEN:
        source_emoji = {
            ForwardSourceType.BOT: "🤖",
            ForwardSourceType.USER: "👤",
            ForwardSourceType.CHANNEL: "📢",
            ForwardSourceType.CHAT: "👥",
        }.get(forward_info["source_type"], "📁")
        source_note = f"\n{source_emoji} Источник: <b>{forward_info['source_name']}</b>"
    
    # Channel backup note - now shows queued status
    channel_note = ""
    if channel_queued:
        queue_size = channel_service.get_queue_size(user_id)
        if queue_size > 1:
            channel_note = f"\n☁️ <i>В очереди на бекап ({queue_size})</i>"
        else:
            channel_note = "\n☁️ <i>Сохраняется в ваш канал...</i>"
    
    # Status
    if not is_new:
        # Track already existed
        if playlist_session:
            await message.reply(
                f"⚠️ Трек уже в твоей библиотеке!\n\n"
                f"🎵 <b>{title}</b>\n"
                f"👤 {artist or 'Неизвестный исполнитель'}\n\n"
                f"Добавить в плейлист «{playlist_session.name}»?",
                reply_markup=get_duplicate_keyboard(track_id)
            )
        else:
            await message.reply(
                "⚠️ Этот трек уже есть в твоей библиотеке!\n\n"
                f"🎵 <b>{title}</b>\n"
                f"👤 {artist or 'Неизвестный исполнитель'}",
                reply_markup=get_track_keyboard(track_id)
            )
        return
    
    # New track added
    if playlist_session:
        playlist_session.add_track(track_id)
        await message.reply(
            f"✅ Трек добавлен в плейлист «{playlist_session.name}»!\n\n"
            f"🎵 <b>{title}</b>\n"
            f"👤 {artist or 'Неизвестный исполнитель'}\n"
            f"⏱ {duration_str}{source_note}\n\n"
            f"📊 Всего в плейлисте: <b>{playlist_session.track_count}</b> треков",
            reply_markup=get_playlist_mode_keyboard(playlist_session.track_count)
        )
    else:
        await message.reply(
            f"✅ <b>Трек добавлен в библиотеку!</b>\n\n"
            f"🎵 <b>{title}</b>\n"
            f"👤 {artist or 'Неизвестный исполнитель'}\n"
            f"⏱ {duration_str} • {size_mb:.1f} MB{source_note}{channel_note}\n\n"
            f"🔄 <i>Метаданные загружаются...</i>",
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

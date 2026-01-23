"""
TG Player Bot - Audio Handler
Supports global shared library with deduplication
"""
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.config import get_settings
from shared.database import get_session
from shared.models import User, Track, Playlist, PlaylistTrack, UserLibrary

from services.session import session_manager


def extract_forward_info(message: Message) -> dict:
    """
    Extract forward source information from a message.
    Returns dict with forward_from_id, forward_from_username, forward_from_name, forward_from_type
    """
    info = {
        "forward_from_id": None,
        "forward_from_username": None,
        "forward_from_name": None,
        "forward_from_type": None,
    }
    
    # Check for forwarded from user/bot
    if message.forward_from:
        user = message.forward_from
        info["forward_from_id"] = user.id
        info["forward_from_username"] = user.username
        info["forward_from_name"] = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username
        info["forward_from_type"] = "bot" if user.is_bot else "user"
    
    # Check for forwarded from channel/chat
    elif message.forward_from_chat:
        chat = message.forward_from_chat
        info["forward_from_id"] = chat.id
        info["forward_from_username"] = chat.username
        info["forward_from_name"] = chat.title or chat.username
        info["forward_from_type"] = chat.type  # channel, supergroup, etc.
    
    # Hidden forward (privacy settings)
    elif message.forward_sender_name:
        info["forward_from_name"] = message.forward_sender_name
        info["forward_from_type"] = "hidden"
    
    return info


async def get_or_create_source_playlist(session, user_id: int, forward_info: dict) -> Playlist | None:
    """
    Get or create an auto-source playlist for the given forward source.
    Returns None if there's no forward info.
    """
    if not forward_info["forward_from_type"]:
        return None
    
    source_id = forward_info["forward_from_id"]
    source_type = forward_info["forward_from_type"]
    source_name = forward_info["forward_from_name"] or "Unknown"
    
    # For hidden forwards, we can't create a meaningful playlist
    if source_type == "hidden":
        return None
    
    # Look for existing auto-source playlist
    playlist = await session.scalar(
        select(Playlist).where(
            and_(
                Playlist.user_id == user_id,
                Playlist.is_auto_source == True,
                Playlist.source_id == source_id
            )
        )
    )
    
    if playlist:
        return playlist
    
    # Create new auto-source playlist
    emoji = {
        "bot": "🤖",
        "user": "👤", 
        "channel": "📢",
        "supergroup": "👥",
    }.get(source_type, "📁")
    
    playlist = Playlist(
        user_id=user_id,
        name=f"{emoji} {source_name}",
        description=f"Треки от {'бота' if source_type == 'bot' else 'пользователя' if source_type == 'user' else 'канала'} {source_name}",
        is_auto_source=True,
        source_id=source_id,
        source_type=source_type,
    )
    session.add(playlist)
    await session.flush()
    
    return playlist


async def add_track_to_playlist(session, playlist: Playlist, track_id: int) -> bool:
    """Add track to playlist if not already present. Returns True if added."""
    # Check if already in playlist
    existing = await session.scalar(
        select(PlaylistTrack).where(
            and_(
                PlaylistTrack.playlist_id == playlist.id,
                PlaylistTrack.track_id == track_id
            )
        )
    )
    
    if existing:
        return False
    
    # Get next position
    from sqlalchemy import func
    max_pos = await session.scalar(
        select(func.coalesce(func.max(PlaylistTrack.position), 0)).where(
            PlaylistTrack.playlist_id == playlist.id
        )
    )
    
    pt = PlaylistTrack(
        playlist_id=playlist.id,
        track_id=track_id,
        position=max_pos + 1
    )
    session.add(pt)
    await session.flush()
    return True


router = Router()
settings = get_settings()


# NOTE: validate_file_id removed - it was redundant
# When Telegram sends us an audio message, the file is guaranteed to be accessible
# The file_id comes directly from Telegram in the same message
# Validation only makes sense when playing old tracks (handled in API layer)


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
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"✓ Завершить ({track_count} треков)" if track_count > 0 else "✓ Завершить",
                callback_data="playlist:finish"
            ),
            InlineKeyboardButton(
                text="✗ Отменить",
                callback_data="playlist:cancel"
            )
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


def format_duration(seconds: int | None) -> str:
    """Format duration in seconds to MM:SS"""
    if not seconds:
        return "—"
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


@router.message(F.audio)
async def handle_audio(message: Message):
    """
    Handle incoming audio files.
    
    Global library logic:
    1. Check if track already exists globally (by file_unique_id)
    2. If exists: add to user's library (if not already there)
    3. If not exists: create track + add to user's library
    4. If forwarded: auto-create/update source playlist
    """
    audio = message.audio
    user = message.from_user
    user_id = user.id
    
    # Extract forward source info
    forward_info = extract_forward_info(message)
    
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
        
        # Check if track already exists GLOBALLY (not per-user)
        existing_track = await session.scalar(
            select(Track).where(Track.file_unique_id == audio.file_unique_id)
        )
        
        if existing_track:
            # Track exists globally - check if user already has it in their library
            existing_lib = await session.scalar(
                select(UserLibrary).where(
                    UserLibrary.user_id == user_id,
                    UserLibrary.track_id == existing_track.id
                )
            )
            
            if existing_lib:
                # User already has this track
                if playlist_session:
                    await message.reply(
                        f"⚠️ Трек уже в твоей библиотеке!\n\n"
                        f"🎵 <b>{existing_track.title or 'Без названия'}</b>\n"
                        f"👤 {existing_track.artist or 'Неизвестный исполнитель'}\n\n"
                        f"Добавить в плейлист «{playlist_session.name}»?",
                        reply_markup=get_duplicate_keyboard(existing_track.id)
                    )
                else:
                    await message.reply(
                        "⚠️ Этот трек уже есть в твоей библиотеке!\n\n"
                        f"🎵 <b>{existing_track.title or 'Без названия'}</b>\n"
                        f"👤 {existing_track.artist or 'Неизвестный исполнитель'}",
                        reply_markup=get_track_keyboard(existing_track.id)
                    )
                return
            else:
                # Track exists globally but user doesn't have it - add to their library
                lib_entry = UserLibrary(
                    user_id=user_id,
                    track_id=existing_track.id,
                    source="uploaded",  # They uploaded it too
                )
                session.add(lib_entry)
                await session.flush()
                
                track_id = existing_track.id
                
                # Auto-create source playlist if forwarded
                source_playlist = await get_or_create_source_playlist(session, user_id, forward_info)
                if source_playlist:
                    await add_track_to_playlist(session, source_playlist, track_id)
                
                title = existing_track.title or audio.title or "Без названия"
                artist = existing_track.artist or audio.performer or "Неизвестный исполнитель"
                duration = format_duration(existing_track.duration or audio.duration)
                size_mb = (existing_track.file_size or audio.file_size or 0) / (1024 * 1024)
                
                # Note: this track was uploaded by someone else
                uploader_note = ""
                if existing_track.user_id != user_id:
                    uploader_note = "\n\n💡 <i>Этот трек уже был в общей библиотеке!</i>"
                
                # Add source info
                source_note = ""
                auto_playlist_note = ""
                if forward_info["forward_from_type"] and forward_info["forward_from_type"] != "hidden":
                    source_name = forward_info["forward_from_name"] or forward_info["forward_from_username"]
                    source_emoji = {"bot": "🤖", "user": "👤", "channel": "📢"}.get(forward_info["forward_from_type"], "📁")
                    source_note = f"\n{source_emoji} Источник: <b>{source_name}</b>"
                    auto_playlist_note = f"\n📂 <i>Добавлен в авто-плейлист «{source_name}»</i>"
                
                if playlist_session:
                    playlist_session.add_track(track_id)
                    await message.reply(
                        f"✅ Трек добавлен в плейлист «{playlist_session.name}»!\n\n"
                        f"🎵 <b>{title}</b>\n"
                        f"👤 {artist}\n"
                        f"⏱ {duration}{source_note}\n\n"
                        f"📊 Всего в плейлисте: <b>{playlist_session.track_count}</b> треков{uploader_note}",
                        reply_markup=get_playlist_mode_keyboard(playlist_session.track_count)
                    )
                else:
                    await message.reply(
                        f"✅ <b>Трек добавлен в библиотеку!</b>\n\n"
                        f"🎵 <b>{title}</b>\n"
                        f"👤 {artist}\n"
                        f"⏱ {duration} • {size_mb:.1f} MB{source_note}{auto_playlist_note}{uploader_note}",
                        reply_markup=get_track_keyboard(track_id)
                    )
                return
        
        # Track doesn't exist globally - create new track
        track = Track(
            user_id=user_id,
            file_id=audio.file_id,
            file_unique_id=audio.file_unique_id,
            title=audio.title,
            artist=audio.performer,
            album=audio.title if not audio.performer else None,
            duration=audio.duration,
            file_size=audio.file_size,
            mime_type=audio.mime_type,
            is_public=True,  # Default to public for shared library
            # Forward source info
            forward_from_id=forward_info["forward_from_id"],
            forward_from_username=forward_info["forward_from_username"],
            forward_from_name=forward_info["forward_from_name"],
            forward_from_type=forward_info["forward_from_type"],
        )
        
        session.add(track)
        
        try:
            await session.flush()
            track_id = track.id
            
            # Also add to user's library
            lib_entry = UserLibrary(
                user_id=user_id,
                track_id=track_id,
                source="uploaded",
            )
            session.add(lib_entry)
            await session.flush()
            
            # Auto-create source playlist if forwarded
            source_playlist = await get_or_create_source_playlist(session, user_id, forward_info)
            if source_playlist:
                await add_track_to_playlist(session, source_playlist, track_id)
            
        except IntegrityError:
            await session.rollback()
            await message.reply("⚠️ Этот трек уже добавлен!")
            return
    
    # Build response
    title = audio.title or "Без названия"
    artist = audio.performer or "Неизвестный исполнитель"
    duration = format_duration(audio.duration)
    size_mb = (audio.file_size or 0) / (1024 * 1024)
    
    # Add source info to response
    source_note = ""
    if forward_info["forward_from_type"] and forward_info["forward_from_type"] != "hidden":
        source_name = forward_info["forward_from_name"] or forward_info["forward_from_username"] or "Unknown"
        source_emoji = {"bot": "🤖", "user": "👤", "channel": "📢"}.get(forward_info["forward_from_type"], "📁")
        source_note = f"\n{source_emoji} Источник: <b>{source_name}</b>"
    
    if playlist_session:
        playlist_session.add_track(track_id)
        
        await message.reply(
            f"✅ Трек добавлен в плейлист «{playlist_session.name}»!\n\n"
            f"🎵 <b>{title}</b>\n"
            f"👤 {artist}\n"
            f"⏱ {duration}{source_note}\n\n"
            f"📊 Всего в плейлисте: <b>{playlist_session.track_count}</b> треков",
            reply_markup=get_playlist_mode_keyboard(playlist_session.track_count)
        )
    else:
        auto_playlist_note = ""
        if forward_info["forward_from_type"] and forward_info["forward_from_type"] != "hidden":
            source_name = forward_info["forward_from_name"] or forward_info["forward_from_username"]
            auto_playlist_note = f"\n📂 <i>Добавлен в авто-плейлист «{source_name}»</i>"
        
        await message.reply(
            f"✅ <b>Трек добавлен в библиотеку!</b>\n\n"
            f"🎵 <b>{title}</b>\n"
            f"👤 {artist}\n"
            f"⏱ {duration} • {size_mb:.1f} MB{source_note}{auto_playlist_note}\n\n"
            f"🌍 <i>Доступен в общей библиотеке</i>",
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

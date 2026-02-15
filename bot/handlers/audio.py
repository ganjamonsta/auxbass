"""
TG Player Bot - Audio Handler v2

Handles audio file uploads and forwards.
Uses new modular service architecture.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from shared.config import get_settings
from shared.database import get_session
from shared.models import User, Track, LibrarySource, ForwardSourceType, UserChannel
from shared.utils import format_duration

from bot.services import track_service, channel_service
from bot.services.deduplication import (
    deduplication_service, 
    get_approx_bitrate, 
    get_approx_bitrate_raw,
    is_hd_quality_raw,
    is_hd_version,
)
from bot.services.session import session_manager
from bot.handlers.keyboards import (
    get_track_keyboard,
    get_playlist_mode_keyboard,
    get_duplicate_keyboard,
    get_upload_duplicate_keyboard,
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
            info["source_type"] = ForwardSourceType.SUPERGROUP
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
    
    # Determine library source from message
    forward_info = extract_forward_info(message)
    library_source = get_library_source(message)
    
    # Metadata for processing
    title = audio.title
    artist = audio.performer
    duration = audio.duration
    file_size = audio.file_size
    file_name = audio.file_name  # Original filename for fallback display
    
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
    
    # Check for potential duplicates BEFORE saving (by artist/title, not file_unique_id)
    potential_duplicates = await deduplication_service.find_potential_duplicates(
        user_id=user_id,
        artist=artist,
        title=title,
        file_unique_id=audio.file_unique_id,
    )
    
    if potential_duplicates and not playlist_session:
        # Check quality: if uploading HD and library has only regular - auto save
        upload_is_hd = is_hd_quality_raw(duration, file_size, audio.mime_type)
        upload_bitrate = get_approx_bitrate_raw(duration, file_size)
        
        # Check if all duplicates are lower quality
        all_duplicates_lower_quality = False
        if upload_is_hd:
            # HD upload - check if all existing are regular quality
            all_duplicates_lower_quality = all(not is_hd_version(dup) for dup in potential_duplicates)
        elif upload_bitrate:
            # Regular upload - check if we're uploading significantly better quality
            all_duplicates_lower_quality = all(
                (br := get_approx_bitrate(dup)) is not None and upload_bitrate > br * 1.4
                for dup in potential_duplicates
            )
        
        if all_duplicates_lower_quality:
            # Uploading better quality version - save without asking
            pass  # Continue to normal save flow below
        else:
            # Same or lower quality - ask user
            display_title = title or (file_name.rsplit('.', 1)[0] if file_name else "Без названия")
            
            # Show what we're uploading
            upload_meta = []
            if duration:
                m, s = divmod(duration, 60)
                upload_meta.append(f"{m}:{s:02d}")
            if file_size:
                upload_meta.append(f"{file_size / (1024*1024):.1f}MB")
            if upload_bitrate:
                upload_meta.append(f"~{int(upload_bitrate)}kbps")
            upload_meta_str = " • ".join(upload_meta) if upload_meta else ""
            
            # Format duplicate info
            dup_list = []
            for idx, dup in enumerate(potential_duplicates[:3]):
                dup_meta = []
                if dup.duration:
                    m, s = divmod(dup.duration, 60)
                    dup_meta.append(f"{m}:{s:02d}")
                if dup.file_size:
                    dup_meta.append(f"{dup.file_size / (1024*1024):.1f}MB")
                bitrate = get_approx_bitrate(dup)
                if bitrate:
                    dup_meta.append(f"~{int(bitrate)}kbps")
                
                meta_str = " • ".join(dup_meta) if dup_meta else ""
                dup_list.append(
                    f"<b>#{idx+1}</b>: {dup.artist or 'Неизвестный'} - {dup.title or 'Без названия'}\n"
                    f"   └ {meta_str}"
                )
            
            dup_text = "\n".join(dup_list)
            
            # Store pending upload data in session
            session_manager.set_pending_upload(user_id, {
                "file_id": audio.file_id,
                "file_unique_id": audio.file_unique_id,
                "title": title,
                "artist": artist,
                "duration": duration,
                "file_size": file_size,
                "mime_type": audio.mime_type,
                "file_name": file_name,
                "library_source": library_source.value if library_source else None,
                "forward_info": forward_info,
            })
            
            await message.reply(
                f"⚠️ <b>Возможный дубликат!</b>\n\n"
                f"🎵 Вы загружаете: <b>{display_title}</b>\n"
                f"   └ {upload_meta_str}\n"
                f"👤 {artist or 'Неизвестный исполнитель'}\n\n"
                f"📚 Похожие треки в библиотеке:\n{dup_text}\n\n"
                f"<i>Можете прослушать и сравнить перед сохранением</i>",
                reply_markup=get_upload_duplicate_keyboard(audio.file_unique_id, potential_duplicates),
                parse_mode="HTML"
            )
            return
    
    # Save track using service
    result = await track_service.save_track(
        user_id=user_id,
        file_id=audio.file_id,
        file_unique_id=audio.file_unique_id,
        title=title,
        artist=artist,
        duration=duration,
        file_size=file_size,
        mime_type=audio.mime_type,
        file_name=file_name,
        library_source=library_source,
        forward_source_type=forward_info["source_type"],
        forward_source_id=forward_info["source_id"],
        forward_source_name=forward_info["source_name"],
        enrich=True,  # Auto-schedule enrichment
    )
    
    track_id = result.track_id
    is_new = result.is_new
    
    # Check if user has backup channel, queue track for forwarding
    channel_queued = False
    try:
        channel_queued = await channel_service.forward_track_to_channel(
            user_id=user_id,
            track_id=track_id,
            bot=message.bot,
        )
    except Exception as e:
        pass
    
    # Channel backup note - now shows queued status
    channel_note = ""
    if channel_queued:
        queue_size = channel_service.get_queue_size(user_id)
        if queue_size > 1:
            channel_note = f"\n☁️ <i>В очереди на бекап ({queue_size})</i>"
        else:
            channel_note = "\n☁️ <i>Сохраняется в ваш канал...</i>"
    else:
        channel_note = "\n⚠️ <i>Канал не подключен. Используйте /channel, чтобы не потерять библиотеку в случае блокировки бота.</i>"
    
    # Build response
    duration_str = format_duration(duration) if duration else ""
    size_mb = (file_size or 0) / (1024 * 1024)
    
    # Get display title - prefer title, fallback to filename
    def get_display_title():
        if title:
            return title
        if file_name:
            import os
            return os.path.splitext(file_name)[0].strip() or "Без названия"
        return "Без названия"
    
    display_title = get_display_title()
    
    # Source info
    source_note = ""
    if forward_info["source_type"] and forward_info["source_type"] != ForwardSourceType.HIDDEN:
        source_emoji = {
            ForwardSourceType.BOT: "🤖",
            ForwardSourceType.USER: "👤",
            ForwardSourceType.CHANNEL: "📢",
            ForwardSourceType.SUPERGROUP: "👥",
        }.get(forward_info["source_type"], "📁")
        source_note = f"\n{source_emoji} Источник: <b>{forward_info['source_name']}</b>"
    
    # Status
    if not is_new:
        # Track already existed
        if playlist_session:
            await message.reply(
                f"⚠️ Трек уже в твоей библиотеке!\n\n"
                f"🎵 <b>{display_title}</b>\n"
                f"👤 {artist or 'Неизвестный исполнитель'}\n\n"
                f"Добавить в плейлист «{playlist_session.name}»?",
                reply_markup=get_duplicate_keyboard(track_id)
            )
        else:
            await message.reply(
                "⚠️ Этот трек уже есть в твоей библиотеке!\n\n"
                f"🎵 <b>{display_title}</b>\n"
                f"👤 {artist or 'Неизвестный исполнитель'}{channel_note}",
                reply_markup=get_track_keyboard(track_id)
            )
        return
    
    # New track added
    if playlist_session:
        playlist_session.add_track(track_id)
        await message.reply(
            f"✅ Трек добавлен в плейлист «{playlist_session.name}»!\n\n"
            f"🎵 <b>{display_title}</b>\n"
            f"👤 {artist or 'Неизвестный исполнитель'}\n"
            f"⏱ {duration_str}{source_note}\n\n"
            f"📊 Всего в плейлисте: <b>{playlist_session.track_count}</b> треков",
            reply_markup=get_playlist_mode_keyboard(playlist_session.track_count)
        )
    else:
        await message.reply(
            f"✅ <b>Трек добавлен в библиотеку!</b>\n\n"
            f"🎵 <b>{display_title}</b>\n"
            f"👤 {artist or 'Неизвестный исполнитель'}\n"
            f"⏱ {duration_str} • {size_mb:.1f} MB{source_note}{channel_note}\n\n"
            f"🔄 <i>Метаданные загружаются...</i>",
            reply_markup=get_track_keyboard(track_id)
        )


# ========== Upload Duplicate Callbacks ==========

@router.callback_query(F.data.startswith("upload_dup:"))
async def handle_upload_dup_callback(callback: CallbackQuery):
    """Handle upload duplicate confirmation callbacks"""
    user_id = callback.from_user.id
    action = callback.data.split(":")[1]
    
    if action == "listen":
        # Listen to existing track for comparison
        track_id = int(callback.data.split(":")[2])
        async with get_session() as session:
            track = await session.get(Track, track_id)
            if track:
                await callback.message.reply_audio(
                    track.file_id,
                    caption=f"🎧 Существующий трек:\n{track.artist or 'Неизвестный'} - {track.title or 'Без названия'}"
                )
        await callback.answer()
    
    elif action == "save":
        # User confirmed - save the track anyway
        pending = session_manager.get_pending_upload(user_id)
        
        # If pending data expired, try to recover from original message
        if not pending:
            # Get original audio message (reply_to_message of bot's duplicate warning)
            original_message = callback.message.reply_to_message
            if original_message and original_message.audio:
                audio = original_message.audio
                # Reconstruct pending data from original message
                pending = {
                    "file_id": audio.file_id,
                    "file_unique_id": audio.file_unique_id,
                    "title": audio.title,
                    "artist": audio.performer,
                    "duration": audio.duration,
                    "file_size": audio.file_size,
                    "file_name": audio.file_name,
                    "library_source": get_library_source(original_message).value,
                    "forward_info": extract_forward_info(original_message),
                }
            else:
                await callback.answer("Загрузка устарела, отправьте трек ещё раз", show_alert=True)
                return
        
        # Parse library source back from string
        lib_source = LibrarySource.UPLOADED
        if pending.get("library_source"):
            try:
                lib_source = LibrarySource(pending["library_source"])
            except ValueError:
                pass
        
        forward_info = pending.get("forward_info", {})
        
        # Save the track
        result = await track_service.save_track(
            user_id=user_id,
            file_id=pending["file_id"],
            file_unique_id=pending["file_unique_id"],
            title=pending.get("title"),
            artist=pending.get("artist"),
            duration=pending.get("duration"),
            file_size=pending.get("file_size"),
            mime_type=pending.get("mime_type"),
            file_name=pending.get("file_name"),
            library_source=lib_source,
            forward_source_type=forward_info.get("source_type"),
            forward_source_id=forward_info.get("source_id"),
            forward_source_name=forward_info.get("source_name"),
            enrich=True,
        )
        
        session_manager.clear_pending_upload(user_id)
        
        # Queue for channel backup
        try:
            await channel_service.forward_track_to_channel(
                user_id=user_id,
                track_id=result.track_id,
                bot=callback.bot,
            )
        except Exception:
            pass
        
        display_title = pending.get("title") or "Без названия"
        
        await callback.message.edit_text(
            f"✅ <b>Трек сохранён!</b>\n\n"
            f"🎵 <b>{display_title}</b>\n"
            f"👤 {pending.get('artist') or 'Неизвестный исполнитель'}\n\n"
            f"🔄 <i>Метаданные загружаются...</i>",
            reply_markup=get_track_keyboard(result.track_id)
        )
        await callback.answer("Трек сохранён!")
    
    elif action == "cancel":
        # User cancelled upload
        session_manager.clear_pending_upload(user_id)
        await callback.message.edit_text("❌ Загрузка отменена.")
        await callback.answer()


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

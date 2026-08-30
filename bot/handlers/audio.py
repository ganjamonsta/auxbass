"""
TG Player Bot - Clean Audio & Document Handler

Handles:
- Single audio file upload
- Batch / Album audio upload with debouncing
- Audio sent as Document (FLAC, WAV, MP3 etc.)
- Telegram Desktop JSON export import (result.json)
"""
import io
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, Document, Audio
from sqlalchemy import select

from shared.config import get_settings
from shared.database import get_session
from shared.models import User, LibrarySource, ForwardSourceType
from shared.utils import format_duration

from bot.services import track_service, channel_service
from bot.services.importer import channel_importer
from bot.handlers.menu_keyboards import get_webapp_keyboard, get_track_keyboard

router = Router()
settings = get_settings()
logger = logging.getLogger(__name__)

# User batch tracking for debounced multi-file uploads: user_id -> BatchTracker
_batch_lock = asyncio.Lock()
_user_batches: Dict[int, dict] = {}


def extract_forward_info(message: Message) -> dict:
    """Extract forward source information from a message."""
    info = {
        "source_type": None,
        "source_id": None,
        "source_name": None,
    }
    if message.forward_from:
        u = message.forward_from
        info["source_type"] = ForwardSourceType.BOT if u.is_bot else ForwardSourceType.USER
        info["source_id"] = u.id
        info["source_name"] = (f"{u.first_name or ''} {u.last_name or ''}".strip() or u.username or str(u.id))
    elif message.forward_from_chat:
        chat = message.forward_from_chat
        info["source_type"] = ForwardSourceType.CHANNEL if chat.type == "channel" else ForwardSourceType.SUPERGROUP
        info["source_id"] = chat.id
        info["source_name"] = chat.title or chat.username or str(chat.id)
    elif message.forward_sender_name:
        info["source_type"] = ForwardSourceType.HIDDEN
        info["source_name"] = message.forward_sender_name
    return info


def get_library_source(message: Message) -> LibrarySource:
    """Determine library source from message"""
    if message.forward_from or message.forward_from_chat or message.forward_sender_name:
        return LibrarySource.SHARED
    return LibrarySource.UPLOADED


# ───────────────────── JSON Export Import ─────────────────────

@router.message(F.document, F.document.file_name.lower().endswith(".json"))
async def handle_json_document(message: Message):
    """Handle Telegram Desktop export JSON upload"""
    doc: Document = message.document
    if doc.file_size and doc.file_size > 50 * 1024 * 1024:
        await message.reply("❌ Файл слишком большой (максимум 50 MB).")
        return

    status_msg = await message.reply("⏳ Загружаю и анализирую файл экспорта...")
    
    try:
        file_io = io.BytesIO()
        await message.bot.download(doc.file_id, destination=file_io)
        file_bytes = file_io.getvalue()
        json_data = json.loads(file_bytes.decode("utf-8", errors="ignore"))
    except Exception as e:
        logger.error(f"Failed to parse JSON export: {e}")
        await status_msg.edit_text("❌ Не удалось прочитать JSON файл. Убедитесь, что это корректный файл экспорта.")
        return

    if not isinstance(json_data, dict) or "messages" not in json_data:
        await status_msg.edit_text(
            "❌ Файл не похож на экспорт чата Telegram Desktop.\n\n"
            "Экспортируйте историю канала через Telegram Desktop (меню ⋮ -> Экспорт истории чата -> формат JSON)."
        )
        return

    last_update_time = 0

    async def on_progress(current: int, total: int, current_track: str):
        nonlocal last_update_time
        now = asyncio.get_event_loop().time()
        if now - last_update_time >= 1.5 or current == total:
            last_update_time = now
            pct = int((current / total) * 100) if total else 0
            try:
                await status_msg.edit_text(
                    f"📥 <b>Импорт музыки из экспорта... ({pct}%)</b>\n\n"
                    f"Обработано: <b>{current}</b> из <b>{total}</b>\n"
                    f"🎵 <i>{current_track[:40]}</i>"
                )
            except Exception:
                pass

    res = await channel_importer.import_from_json(
        user_id=message.from_user.id,
        json_data=json_data,
        bot=message.bot,
        progress_callback=on_progress,
    )

    if not res.get("success"):
        await status_msg.edit_text(f"❌ Ошибка импорта:\n{res.get('error', 'Неизвестная ошибка')}")
        return

    total = res["total"]
    imported = res["imported"]
    skipped = res["skipped"]

    await status_msg.edit_text(
        f"🎉 <b>Импорт успешно завершён!</b>\n\n"
        f"✅ Добавлено новых треков: <b>{imported}</b>\n"
        f"⏭ Уже было в библиотеке: <b>{skipped}</b>\n"
        f"📊 Всего в файле: <b>{total}</b>\n\n"
        "Обложки и метаданные подтягиваются в фоновом режиме.",
        reply_markup=get_webapp_keyboard(),
    )


# ───────────────────── Audio Batch Processing ─────────────────────

async def _save_audio_item(
    user_id: int,
    audio_obj: Audio | Document,
    forward_info: dict,
    library_source: LibrarySource,
    bot,
) -> tuple[int, bool, str, str]:
    """Helper to save a single track and return (track_id, is_new, title, artist)"""
    title = getattr(audio_obj, "title", None)
    artist = getattr(audio_obj, "performer", None)
    duration = getattr(audio_obj, "duration", None)
    file_size = getattr(audio_obj, "file_size", None)
    file_name = getattr(audio_obj, "file_name", None)
    mime_type = getattr(audio_obj, "mime_type", None)

    # Save to library
    res = await track_service.save_track(
        user_id=user_id,
        file_id=audio_obj.file_id,
        file_unique_id=audio_obj.file_unique_id,
        title=title,
        artist=artist,
        duration=duration,
        file_size=file_size,
        mime_type=mime_type,
        file_name=file_name,
        library_source=library_source,
        forward_source_type=forward_info["source_type"],
        forward_source_id=forward_info["source_id"],
        forward_source_name=forward_info["source_name"],
        enrich=True,
    )

    # Forward to channel in background if configured
    try:
        await channel_service.forward_track_to_channel(
            user_id=user_id,
            track_id=res.track_id,
            bot=bot,
        )
    except Exception:
        pass

    display_title = title or (file_name.rsplit(".", 1)[0] if file_name else "Без названия")
    display_artist = artist or "Неизвестный исполнитель"
    return res.track_id, res.is_new, display_title, display_artist


async def _batch_timer_worker(user_id: int, bot):
    """Wait for debounce timeout and send consolidated batch confirmation"""
    await asyncio.sleep(1.8)
    
    async with _batch_lock:
        batch = _user_batches.pop(user_id, None)

    if not batch:
        return

    count = batch["count"]
    target_msg: Message = batch["target_msg"]
    first_title = batch.get("first_title", "")
    first_artist = batch.get("first_artist", "")
    new_count = batch["new_count"]

    if count == 1:
        # Single track response
        dur_str = format_duration(batch.get("duration", 0))
        size_mb = (batch.get("file_size", 0) or 0) / (1024 * 1024)
        meta_sub = f"⏱ {dur_str} • {size_mb:.1f} MB" if dur_str else f"{size_mb:.1f} MB"

        await target_msg.reply(
            f"🎵 <b>{first_artist}</b> — <b>{first_title}</b>\n"
            f"└ {meta_sub}\n\n"
            f"✅ Добавлено в медиатеку",
            reply_markup=get_track_keyboard(batch.get("first_track_id")),
        )
    else:
        # Batch response
        await target_msg.reply(
            f"✅ <b>Добавлено {count} треков в библиотеку!</b>\n\n"
            f"🎵 Новых: <b>{new_count}</b> (дубликатов пропущено: <b>{count - new_count}</b>)\n"
            f"✨ Метаданные и обложки обновляются в фоне.",
            reply_markup=get_webapp_keyboard(),
        )


# ───────────────────── Audio Handlers ─────────────────────

@router.message(F.audio)
async def handle_audio(message: Message):
    """Handle regular audio messages (single or batches)"""
    user_id = message.from_user.id
    audio = message.audio

    forward_info = extract_forward_info(message)
    lib_source = get_library_source(message)

    track_id, is_new, display_title, display_artist = await _save_audio_item(
        user_id=user_id,
        audio_obj=audio,
        forward_info=forward_info,
        library_source=lib_source,
        bot=message.bot,
    )

    async with _batch_lock:
        if user_id not in _user_batches:
            _user_batches[user_id] = {
                "count": 1,
                "new_count": 1 if is_new else 0,
                "target_msg": message,
                "first_track_id": track_id,
                "first_title": display_title,
                "first_artist": display_artist,
                "duration": audio.duration,
                "file_size": audio.file_size,
                "task": asyncio.create_task(_batch_timer_worker(user_id, message.bot)),
            }
        else:
            b = _user_batches[user_id]
            b["count"] += 1
            if is_new:
                b["new_count"] += 1
            b["target_msg"] = message
            b["task"].cancel()
            b["task"] = asyncio.create_task(_batch_timer_worker(user_id, message.bot))


@router.message(F.document)
async def handle_audio_document(message: Message):
    """Handle audio sent as file/document (e.g. uncompressed FLAC/WAV/MP3)"""
    doc: Document = message.document
    fn = (doc.file_name or "").lower()
    mime = (doc.mime_type or "").lower()

    is_audio_file = (
        mime.startswith("audio/")
        or fn.endswith((".mp3", ".flac", ".m4a", ".ogg", ".opus", ".wav", ".aac", ".alac"))
    )

    if not is_audio_file:
        return  # Ignore non-audio documents (JSON handled above)

    user_id = message.from_user.id
    forward_info = extract_forward_info(message)
    lib_source = get_library_source(message)

    track_id, is_new, display_title, display_artist = await _save_audio_item(
        user_id=user_id,
        audio_obj=doc,
        forward_info=forward_info,
        library_source=lib_source,
        bot=message.bot,
    )

    async with _batch_lock:
        if user_id not in _user_batches:
            _user_batches[user_id] = {
                "count": 1,
                "new_count": 1 if is_new else 0,
                "target_msg": message,
                "first_track_id": track_id,
                "first_title": display_title,
                "first_artist": display_artist,
                "duration": 0,
                "file_size": doc.file_size,
                "task": asyncio.create_task(_batch_timer_worker(user_id, message.bot)),
            }
        else:
            b = _user_batches[user_id]
            b["count"] += 1
            if is_new:
                b["new_count"] += 1
            b["target_msg"] = message
            b["task"].cancel()
            b["task"] = asyncio.create_task(_batch_timer_worker(user_id, message.bot))

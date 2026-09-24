"""
TG Player - Telegram Desktop JSON Export Importer

Imports audio files from Telegram Desktop channel/chat exports (result.json).
Fast and targeted: only accesses messages that actually contain audio tracks.
"""
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from sqlalchemy import select

from shared.database import get_session
from shared.models import (
    User, UserChannel, ChannelMessage, ChannelMessageStatus,
    Track, UserLibrary, LibrarySource, ForwardSourceType, utcnow
)
from shared.matching import clean_track_metadata, normalize_artist
from shared.config import get_settings
from bot.services.tracks.service import sanitize_artist
from bot.services.channels import channel_service
from bot.services.enrichment import enrichment_worker

logger = logging.getLogger(__name__)


@dataclass
class ExportAudioItem:
    message_id: int
    title: Optional[str]
    performer: Optional[str]
    duration_seconds: Optional[int]
    file_name: Optional[str]
    mime_type: Optional[str]


def parse_telegram_export_json(data: Dict[str, Any]) -> tuple[Optional[str], Optional[int], List[ExportAudioItem]]:
    """
    Parse Telegram Desktop JSON export.
    
    Returns:
        (channel_name, channel_id, list of ExportAudioItem)
    """
    channel_name = data.get("name")
    raw_id = data.get("id")
    channel_id = None
    if raw_id is not None:
        try:
            # Telegram export id is usually positive int (e.g. 1234567890)
            # Channel ID in bot API format has -100 prefix: -1001234567890
            c_id = int(str(raw_id).replace("channel", ""))
            if c_id > 0:
                channel_id = -int(f"100{c_id}")
            else:
                channel_id = c_id
        except Exception:
            channel_id = None

    messages = data.get("messages", [])
    audio_items: List[ExportAudioItem] = []

    for msg in messages:
        if not isinstance(msg, dict):
            continue
        
        msg_id = msg.get("id")
        if not msg_id:
            continue

        media_type = msg.get("media_type")
        file_path = msg.get("file", "") or ""
        mime_type = msg.get("mime_type", "") or ""
        
        is_audio = (
            media_type == "audio_file"
            or mime_type.startswith("audio/")
            or file_path.lower().endswith((".mp3", ".flac", ".m4a", ".ogg", ".opus", ".wav", ".aac"))
            or ("performer" in msg and "duration_seconds" in msg)
        )

        if not is_audio:
            continue

        audio_items.append(
            ExportAudioItem(
                message_id=msg_id,
                title=msg.get("title") or msg.get("name"),
                performer=msg.get("performer") or msg.get("artist"),
                duration_seconds=msg.get("duration_seconds") or msg.get("duration"),
                file_name=msg.get("file_name") or (file_path.split("/")[-1] if file_path else None),
                mime_type=mime_type or "audio/mpeg",
            )
        )

    return channel_name, channel_id, audio_items


class ChannelImporter:
    """Service to import channel export data into TG Player library"""

    async def import_from_json(
        self,
        user_id: int,
        json_data: Dict[str, Any],
        bot: Bot,
        progress_callback: Optional[Callable[[int, int, str], Any]] = None,
    ) -> Dict[str, Any]:
        """
        Import tracks from parsed export JSON into user's library.
        Only reaches out to Telegram for exact audio message IDs.
        """
        ch_name, parsed_ch_id, audio_items = parse_telegram_export_json(json_data)
        
        if not audio_items:
            return {
                "success": False,
                "error": "В файле экспорта не найдено аудиозаписей.",
                "total": 0,
                "imported": 0,
            }

        # Check if user has a configured channel
        user_channel = await channel_service.get_user_channel(user_id)
        target_channel_id = None
        
        if user_channel:
            target_channel_id = user_channel.channel_id
        elif parsed_ch_id:
            # Check if bot has access to parsed channel
            success, title, _ = await channel_service.verify_channel_access(parsed_ch_id, bot)
            if success:
                user_channel = await channel_service.setup_channel(
                    user_id=user_id,
                    channel_id=parsed_ch_id,
                    channel_title=title or ch_name,
                    bot=bot,
                )
                target_channel_id = parsed_ch_id

        if not target_channel_id:
            return {
                "success": False,
                "error": "Сначала подключите ваш канал к боту через меню '☁️ Мой канал'.",
                "total": len(audio_items),
                "imported": 0,
            }

        total = len(audio_items)
        imported = 0
        skipped = 0

        # Check existing channel messages to skip already indexed tracks
        async with get_session() as session:
            existing_messages = await session.scalars(
                select(ChannelMessage.message_id).where(
                    ChannelMessage.channel_id == user_channel.id,
                    ChannelMessage.status == ChannelMessageStatus.SENT,
                )
            )
            known_msg_ids = set(existing_messages.all())

        BATCH_SIZE = 100
        batch_items: List[ExportAudioItem] = []

        for idx, item in enumerate(audio_items, start=1):
            if item.message_id in known_msg_ids:
                skipped += 1
                continue

            batch_items.append(item)

            if len(batch_items) >= BATCH_SIZE:
                saved = await self._save_lazy_items_batch(
                    user_id=user_id,
                    user_channel_id=user_channel.id,
                    target_channel_id=target_channel_id,
                    channel_title=user_channel.channel_title or ch_name,
                    items=batch_items,
                )
                imported += saved
                batch_items.clear()

                if progress_callback:
                    try:
                        await progress_callback(
                            idx, total, f"{item.performer or 'Неизвестный'} - {item.title or item.file_name or 'Аудио'}"
                        )
                    except Exception:
                        pass
                
                # Tiny yield to avoid blocking the event loop on huge imports
                await asyncio.sleep(0.005)

        # Flush remaining items
        if batch_items:
            saved = await self._save_lazy_items_batch(
                user_id=user_id,
                user_channel_id=user_channel.id,
                target_channel_id=target_channel_id,
                channel_title=user_channel.channel_title or ch_name,
                items=batch_items,
            )
            imported += saved
            batch_items.clear()

        if progress_callback:
            try:
                await progress_callback(total, total, "Готово!")
            except Exception:
                pass

        logger.info(
            f"[JSON Import] Completed lazy import for user {user_id}: "
            f"imported={imported}, skipped={skipped}, total={total}"
        )

        return {
            "success": True,
            "total": total,
            "imported": imported,
            "skipped": skipped,
            "failed": 0,
        }

    async def _save_lazy_items_batch(
        self,
        user_id: int,
        user_channel_id: int,
        target_channel_id: int,
        channel_title: Optional[str],
        items: List[ExportAudioItem],
    ) -> int:
        """Save a batch of audio items as lazy tracks with ChannelMessage links in a single transaction."""
        imported_count = 0
        async with get_session() as session:
            # Ensure user exists
            user = await session.get(User, user_id)
            if not user:
                user = User(id=user_id)
                session.add(user)
                await session.flush()

            for item in items:
                lazy_file_id = f"lazy:{target_channel_id}:{item.message_id}"
                lazy_unique_id = f"lazy_{target_channel_id}_{item.message_id}"

                # Check if track already exists by file_unique_id
                existing_track = await session.scalar(
                    select(Track).where(Track.file_unique_id == lazy_unique_id)
                )

                if existing_track:
                    track = existing_track
                else:
                    clean_title, clean_artist = clean_track_metadata(item.title, item.performer, item.file_name)
                    title = clean_title or item.file_name or "Без названия"
                    artist = clean_artist or "Неизвестный исполнитель"
                    sanitized = sanitize_artist(artist)
                    normalized = normalize_artist(sanitized) if sanitized else None

                    track = Track(
                        file_id=lazy_file_id,
                        file_unique_id=lazy_unique_id,
                        title=title,
                        artist=sanitized,
                        normalized_artist=normalized,
                        duration=item.duration_seconds,
                        mime_type=item.mime_type or "audio/mpeg",
                        file_name=item.file_name,
                        uploader_id=user_id,
                        is_public=True,
                        forward_source_type=ForwardSourceType.CHANNEL,
                        forward_source_id=target_channel_id,
                        forward_source_name=channel_title,
                    )
                    session.add(track)
                    await session.flush()

                # Add to UserLibrary if not already present
                lib_entry = await session.scalar(
                    select(UserLibrary).where(
                        UserLibrary.user_id == user_id,
                        UserLibrary.track_id == track.id,
                    )
                )
                if not lib_entry:
                    lib_entry = UserLibrary(
                        user_id=user_id,
                        track_id=track.id,
                        source=LibrarySource.UPLOADED,
                    )
                    session.add(lib_entry)

                # Link ChannelMessage
                ch_msg = await session.scalar(
                    select(ChannelMessage).where(
                        ChannelMessage.channel_id == user_channel_id,
                        ChannelMessage.track_id == track.id,
                    )
                )
                if not ch_msg:
                    ch_msg = ChannelMessage(
                        channel_id=user_channel_id,
                        track_id=track.id,
                        message_id=item.message_id,
                        status=ChannelMessageStatus.SENT,
                    )
                    session.add(ch_msg)
                else:
                    ch_msg.message_id = item.message_id
                    ch_msg.status = ChannelMessageStatus.SENT

                imported_count += 1

            await session.commit()
            enrichment_worker.notify_new_track()

        return imported_count


channel_importer = ChannelImporter()

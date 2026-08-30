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
    UserChannel, ChannelMessage, ChannelMessageStatus,
    Track, UserLibrary, LibrarySource, ForwardSourceType, utcnow
)
from shared.config import get_settings
from bot.services.tracks import track_service
from bot.services.channels import channel_service

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

        settings = get_settings()
        buffer_chat_id = settings.scanner_buffer_chat_id or user_id
        
        total = len(audio_items)
        imported = 0
        skipped = 0
        failed = 0

        # Check existing channel messages to skip already indexed tracks
        async with get_session() as session:
            existing_messages = await session.scalars(
                select(ChannelMessage.message_id).where(
                    ChannelMessage.channel_id == user_channel.id,
                    ChannelMessage.status == ChannelMessageStatus.SENT,
                )
            )
            known_msg_ids = set(existing_messages.all())

        delete_buffer_ids: List[int] = []

        for idx, item in enumerate(audio_items, start=1):
            if item.message_id in known_msg_ids:
                skipped += 1
                continue

            if progress_callback and (idx % 5 == 0 or idx == total or idx == 1):
                try:
                    await progress_callback(
                        idx, total, f"{item.performer or 'Неизвестный'} - {item.title or item.file_name or 'Аудио'}"
                    )
                except Exception:
                    pass

            forwarded = None
            try:
                # Forward single target audio message to buffer chat to read its file_id & file_unique_id
                forwarded = await bot.forward_message(
                    chat_id=buffer_chat_id,
                    from_chat_id=target_channel_id,
                    message_id=item.message_id,
                    disable_notification=True,
                )
            except TelegramRetryAfter as e:
                logger.warning(f"Rate limited during import: wait {e.retry_after}s")
                await asyncio.sleep(e.retry_after + 1)
                try:
                    forwarded = await bot.forward_message(
                        chat_id=buffer_chat_id,
                        from_chat_id=target_channel_id,
                        message_id=item.message_id,
                        disable_notification=True,
                    )
                except Exception:
                    failed += 1
                    continue
            except TelegramBadRequest as e:
                logger.debug(f"Message {item.message_id} not accessible in channel: {e}")
                failed += 1
                continue
            except TelegramForbiddenError:
                return {
                    "success": False,
                    "error": "Бот потерял доступ к каналу (проверьте права администратора).",
                    "total": total,
                    "imported": imported,
                }
            except Exception as e:
                logger.error(f"Error fetching message {item.message_id}: {e}")
                failed += 1
                continue

            if forwarded and forwarded.audio:
                delete_buffer_ids.append(forwarded.message_id)
                audio = forwarded.audio

                # Save track into database
                result = await track_service.save_track(
                    user_id=user_id,
                    file_id=audio.file_id,
                    file_unique_id=audio.file_unique_id,
                    title=item.title or audio.title,
                    artist=item.performer or audio.performer,
                    duration=item.duration_seconds or audio.duration,
                    file_size=audio.file_size,
                    mime_type=audio.mime_type or item.mime_type,
                    file_name=item.file_name or audio.file_name,
                    library_source=LibrarySource.UPLOADED,
                    forward_source_type=ForwardSourceType.CHANNEL,
                    forward_source_id=target_channel_id,
                    forward_source_name=user_channel.channel_title or ch_name,
                    enrich=True,
                )

                # Link channel message
                async with get_session() as session:
                    ch_msg = await session.scalar(
                        select(ChannelMessage).where(
                            ChannelMessage.channel_id == user_channel.id,
                            ChannelMessage.track_id == result.track_id,
                        )
                    )
                    if not ch_msg:
                        ch_msg = ChannelMessage(
                            channel_id=user_channel.id,
                            track_id=result.track_id,
                            message_id=item.message_id,
                            status=ChannelMessageStatus.SENT,
                        )
                        session.add(ch_msg)
                    else:
                        ch_msg.message_id = item.message_id
                        ch_msg.status = ChannelMessageStatus.SENT
                    await session.commit()

                known_msg_ids.add(item.message_id)
                imported += 1
            else:
                if forwarded:
                    delete_buffer_ids.append(forwarded.message_id)
                failed += 1

            # Clean buffer chat periodically in batches
            if len(delete_buffer_ids) >= 30:
                try:
                    await bot.delete_messages(chat_id=buffer_chat_id, message_ids=delete_buffer_ids)
                except Exception:
                    pass
                delete_buffer_ids.clear()

            # Small delay to keep Telegram API happy
            await asyncio.sleep(0.3)

        # Cleanup leftover buffer messages
        if delete_buffer_ids:
            try:
                await bot.delete_messages(chat_id=buffer_chat_id, message_ids=delete_buffer_ids)
            except Exception:
                pass

        return {
            "success": True,
            "total": total,
            "imported": imported,
            "skipped": skipped,
            "failed": failed,
        }


channel_importer = ChannelImporter()

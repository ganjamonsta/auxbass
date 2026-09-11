"""
TG Player Bot - Download Handlers
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.services.delivery import (
    deliver_single_track,
    deliver_playlist_tracks,
    deliver_album_tracks,
)

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith("download_track:"))
async def handle_download_track(callback: CallbackQuery):
    """Handle single track download"""
    track_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id if callback.message else user_id

    success = await deliver_single_track(
        callback.bot,
        chat_id=chat_id,
        track_id=track_id,
        user_id=user_id,
        reply_to_message_id=callback.message.message_id if callback.message else None
    )
    if success:
        await callback.answer("Отправлено!")
    else:
        await callback.answer("Трек не найден или недоступен", show_alert=True)


@router.callback_query(F.data.startswith("download_playlist:"))
async def handle_download_playlist(callback: CallbackQuery):
    """Handle playlist download (send all tracks)"""
    playlist_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id if callback.message else user_id

    await callback.answer("Отправляю плейлист...")
    sent = await deliver_playlist_tracks(
        callback.bot,
        chat_id=chat_id,
        playlist_id=playlist_id,
        user_id=user_id,
        reply_to_message_id=callback.message.message_id if callback.message else None
    )
    if not sent:
        await callback.answer("Не удалось отправить плейлист или он пуст", show_alert=True)


@router.callback_query(F.data.startswith("download_album:"))
async def handle_download_album(callback: CallbackQuery):
    """Handle album download (send all tracks)"""
    album_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id if callback.message else user_id

    await callback.answer("Отправляю альбом...")
    sent = await deliver_album_tracks(
        callback.bot,
        chat_id=chat_id,
        album_id=album_id,
        user_id=user_id,
        reply_to_message_id=callback.message.message_id if callback.message else None
    )
    if not sent:
        await callback.answer("Не удалось отправить альбом или он пуст", show_alert=True)

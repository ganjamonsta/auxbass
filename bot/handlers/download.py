"""
TG Player Bot - Download Handlers
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import asyncio

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import get_session
from shared.models import Track, Playlist, PlaylistTrack

router = Router()

@router.callback_query(F.data.startswith("download_track:"))
async def handle_download_track(callback: CallbackQuery):
    """Handle single track download"""
    track_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    async with get_session() as session:
        track = await session.scalar(
            select(Track).where(
                Track.id == track_id,
                # Depending on requirement, we might allow downloading any track if public,
                # but currently models seem to link tracks to users. 
                # Assuming user can only download their own tracks or we don't care about ownership for download 
                # (since they have the button they probably can see it).
                # But safer to check accessing user has rights or it is their track.
                # However, for simplicity and assuming buttons are only shown to owner:
                Track.user_id == user_id
            )
        )
        
        if not track:
            await callback.answer("Трек не найден", show_alert=True)
            return

        # Send audio using file_id (instant forward-like behavior)
        caption = f"🎧 {track.artist or 'Неизвестен'} - {track.title or 'Без названия'}"
        await callback.message.answer_audio(
            audio=track.file_id,
            caption=caption,
            duration=track.duration,
            performer=track.artist,
            title=track.title
        )
        await callback.answer("Отправлено!")

@router.callback_query(F.data.startswith("download_playlist:"))
async def handle_download_playlist(callback: CallbackQuery):
    """Handle playlist download (send all tracks)"""
    playlist_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    async with get_session() as session:
        playlist = await session.get(
            Playlist, 
            playlist_id, 
            options=[selectinload(Playlist.track_associations).selectinload(PlaylistTrack.track)]
        )

        if not playlist or playlist.user_id != user_id:
            await callback.answer("Плейлист не найден", show_alert=True)
            return

        tracks = [pt.track for pt in playlist.track_associations]
        if not tracks:
            await callback.answer("Плейлист пуст", show_alert=True)
            return

        await callback.answer("Начинаю отправку...")
        # Reply to the message with status
        status_msg = await callback.message.reply(f"🚀 Начинаю отправку {len(tracks)} треков...")

        for track in tracks:
            if not track.file_id:
                continue
                
            caption = f"🎧 {track.artist or 'Неизвестен'} - {track.title or 'Без названия'}"
            try:
                await callback.message.answer_audio(
                    audio=track.file_id,
                    caption=caption,
                    duration=track.duration,
                    performer=track.artist,
                    title=track.title
                )
                # Small delay to be nice to API limits
                await asyncio.sleep(0.1)
            except Exception as e:
                # Log error or ignore? 
                # If a file_id is invalid, we might want to skip.
                continue
        
        await status_msg.edit_text(f"✅ Готово! Отправлено {len(tracks)} треков.")

"""
TG Player Bot - Download Handlers
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaAudio
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
        result = await session.execute(
            select(Playlist)
            .options(selectinload(Playlist.track_associations).selectinload(PlaylistTrack.track))
            .where(Playlist.id == playlist_id)
        )
        playlist = result.scalar()

        if not playlist or playlist.user_id != user_id:
            await callback.answer("Плейлист не найден", show_alert=True)
            return

        tracks = [pt.track for pt in playlist.track_associations]
        if not tracks:
            await callback.answer("Плейлист пуст", show_alert=True)
            return

        await callback.answer("Отправляю плейлист...")
        
        # Filter tracks with valid file_id
        valid_tracks = [t for t in tracks if t.file_id]
        if not valid_tracks:
            await callback.message.reply("❌ Нет доступных треков для отправки")
            return
        
        # Telegram allows max 10 media per group
        # Send tracks in batches of 10
        batch_size = 10
        total_sent = 0
        
        for i in range(0, len(valid_tracks), batch_size):
            batch = valid_tracks[i:i + batch_size]
            
            # Build media group
            media_group = []
            for idx, track in enumerate(batch):
                # Only first item in group gets caption with playlist name
                caption = None
                if i == 0 and idx == 0:
                    caption = f"📁 Плейлист: {playlist.name}\n🎵 {len(valid_tracks)} треков"
                
                media_group.append(InputMediaAudio(
                    media=track.file_id,
                    caption=caption,
                    performer=track.artist,
                    title=track.title,
                    duration=track.duration
                ))
            
            try:
                await callback.message.answer_media_group(media=media_group)
                total_sent += len(batch)
                # Small delay between batches
                if i + batch_size < len(valid_tracks):
                    await asyncio.sleep(0.5)
            except Exception as e:
                # If media group fails, try sending individually
                for track in batch:
                    try:
                        await callback.message.answer_audio(
                            audio=track.file_id,
                            performer=track.artist,
                            title=track.title,
                            duration=track.duration
                        )
                        total_sent += 1
                        await asyncio.sleep(0.1)
                    except:
                        continue
        
        await callback.message.reply(f"✅ Отправлено {total_sent} треков из плейлиста «{playlist.name}»")

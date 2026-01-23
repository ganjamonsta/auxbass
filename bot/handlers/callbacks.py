"""
TG Player Bot - Callback Query Handlers
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.config import get_settings
from shared.database import get_session
from shared.models import Track, Playlist, PlaylistTrack

from services.session import session_manager


router = Router()
settings = get_settings()


def get_webapp_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with Mini App button"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎵 Открыть плеер",
            web_app=WebAppInfo(url=settings.webapp_url)
        )]
    ])


@router.callback_query(F.data.startswith("delete_track:"))
async def handle_delete_track(callback: CallbackQuery):
    """Handle track deletion"""
    track_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    async with get_session() as session:
        # Find track
        track = await session.scalar(
            select(Track).where(
                Track.id == track_id,
                Track.user_id == user_id
            )
        )
        
        if not track:
            await callback.answer("Трек не найден", show_alert=True)
            return
        
        track_title = track.title or "Без названия"
        await session.delete(track)
    
    await callback.message.edit_text(
        f"🗑 Трек <b>{track_title}</b> удалён из библиотеки."
    )
    await callback.answer("Удалено!")


# ========== Playlist Creation Callbacks ==========

@router.callback_query(F.data == "playlist:finish")
async def handle_playlist_finish(callback: CallbackQuery):
    """Finish playlist creation and save"""
    user_id = callback.from_user.id
    
    playlist_session = session_manager.get_playlist_session(user_id)
    if not playlist_session:
        await callback.answer("Нет активного плейлиста", show_alert=True)
        return
    
    if playlist_session.track_count == 0:
        await callback.answer("Добавь хотя бы один трек!", show_alert=True)
        return
    
    # Create playlist in database
    async with get_session() as session:
        # Create playlist
        playlist = Playlist(
            user_id=user_id,
            name=playlist_session.name,
        )
        session.add(playlist)
        await session.flush()
        
        # Add tracks
        for position, track_id in enumerate(playlist_session.track_ids):
            pt = PlaylistTrack(
                playlist_id=playlist.id,
                track_id=track_id,
                position=position,
            )
            session.add(pt)
        
        playlist_id = playlist.id
    
    # Clear session
    session_manager.end_playlist_session(user_id)
    
    await callback.message.edit_text(
        f"🎉 <b>Плейлист создан!</b>\n\n"
        f"📁 «{playlist_session.name}»\n"
        f"🎵 {playlist_session.track_count} треков\n\n"
        f"Открой плеер, чтобы послушать!",
        reply_markup=get_webapp_keyboard()
    )
    await callback.answer("Плейлист создан!")


@router.callback_query(F.data == "playlist:cancel")
async def handle_playlist_cancel(callback: CallbackQuery):
    """Cancel playlist creation"""
    user_id = callback.from_user.id
    
    playlist_session = session_manager.get_playlist_session(user_id)
    if playlist_session:
        session_manager.end_playlist_session(user_id)
        await callback.message.edit_text(
            f"❌ Создание плейлиста «{playlist_session.name}» отменено.\n\n"
            f"Треки остались в библиотеке."
        )
    else:
        await callback.message.edit_text("❌ Отменено.")
    
    await callback.answer()


@router.callback_query(F.data == "playlist:cancel_input")
async def handle_playlist_cancel_input(callback: CallbackQuery, state: FSMContext):
    """Cancel playlist name input"""
    await state.clear()
    await callback.message.edit_text("❌ Создание плейлиста отменено.")
    await callback.answer()


@router.callback_query(F.data.startswith("playlist:add_existing:"))
async def handle_add_existing_to_playlist(callback: CallbackQuery):
    """Add existing track to playlist being created"""
    user_id = callback.from_user.id
    track_id = int(callback.data.split(":")[2])
    
    playlist_session = session_manager.get_playlist_session(user_id)
    if not playlist_session:
        await callback.answer("Нет активного плейлиста", show_alert=True)
        return
    
    # Check if track already in this playlist session
    if track_id in playlist_session.track_ids:
        await callback.answer("Трек уже в плейлисте!", show_alert=True)
        return
    
    # Add to session
    playlist_session.add_track(track_id)
    
    # Get track info
    async with get_session() as session:
        track = await session.get(Track, track_id)
        title = track.title if track else "Трек"
    
    await callback.message.edit_text(
        f"✅ Трек добавлен в плейлист «{playlist_session.name}»!\n\n"
        f"📊 Всего: <b>{playlist_session.track_count}</b> треков",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✓ Завершить ({playlist_session.track_count} треков)",
                    callback_data="playlist:finish"
                ),
                InlineKeyboardButton(
                    text="✗ Отменить",
                    callback_data="playlist:cancel"
                )
            ]
        ])
    )
    await callback.answer("Добавлено!")


@router.callback_query(F.data == "playlist:skip_duplicate")
async def handle_skip_duplicate(callback: CallbackQuery):
    """Skip duplicate track"""
    user_id = callback.from_user.id
    
    playlist_session = session_manager.get_playlist_session(user_id)
    if playlist_session:
        await callback.message.edit_text(
            f"⏭ Трек пропущен.\n\n"
            f"Продолжай отправлять аудио для плейлиста «{playlist_session.name}»\n"
            f"📊 Сейчас: <b>{playlist_session.track_count}</b> треков",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"✓ Завершить ({playlist_session.track_count} треков)",
                        callback_data="playlist:finish"
                    ),
                    InlineKeyboardButton(
                        text="✗ Отменить",
                        callback_data="playlist:cancel"
                    )
                ]
            ])
        )
    else:
        await callback.message.edit_text("⏭ Пропущено.")
    
    await callback.answer()

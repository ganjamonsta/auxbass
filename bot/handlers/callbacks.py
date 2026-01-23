"""
TG Player Bot - Callback Query Handlers
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

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


# ========== Playlist Management Callbacks ==========

@router.callback_query(F.data.startswith("pl:menu:"))
async def handle_playlist_menu(callback: CallbackQuery):
    """Show playlist management menu"""
    playlist_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id
    
    async with get_session() as session:
        playlist = await session.get(Playlist, playlist_id, options=[selectinload(Playlist.track_associations)])
        
        if not playlist or playlist.user_id != user_id:
            await callback.answer("Плейлист не найден", show_alert=True)
            return
        
        track_count = len(playlist.track_associations) if playlist.track_associations else 0
        playlist_name = playlist.name
        created_at = playlist.created_at.strftime('%d.%m.%Y')
    
    await callback.message.edit_text(
        f"📁 <b>{playlist_name}</b>\n\n"
        f"🎵 Треков: {track_count}\n"
        f"📅 Создан: {created_at}\n\n"
        "Выбери действие:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Переименовать",
                    callback_data=f"pl:rename:{playlist_id}"
                ),
                InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data=f"pl:delete_confirm:{playlist_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎵 Открыть плеер",
                    web_app=WebAppInfo(url=settings.webapp_url)
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад к списку",
                    callback_data="pl:back_to_list"
                )
            ]
        ])
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pl:rename:"))
async def handle_playlist_rename_start(callback: CallbackQuery, state: FSMContext):
    """Start playlist rename process"""
    from handlers.commands import PlaylistStates
    
    playlist_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id
    
    async with get_session() as session:
        playlist = await session.get(Playlist, playlist_id)
        
        if not playlist or playlist.user_id != user_id:
            await callback.answer("Плейлист не найден", show_alert=True)
            return
        
        playlist_name = playlist.name
    
    # Set state for rename
    await state.set_state(PlaylistStates.waiting_for_rename)
    await state.update_data(rename_playlist_id=playlist_id)
    
    await callback.message.edit_text(
        f"✏️ <b>Переименование плейлиста</b>\n\n"
        f"Текущее название: «{playlist_name}»\n\n"
        "Введи новое название:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✗ Отмена",
                callback_data=f"pl:menu:{playlist_id}"
            )]
        ])
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pl:delete_confirm:"))
async def handle_playlist_delete_confirm(callback: CallbackQuery):
    """Show delete confirmation"""
    playlist_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id
    
    async with get_session() as session:
        playlist = await session.get(Playlist, playlist_id, options=[selectinload(Playlist.track_associations)])
        
        if not playlist or playlist.user_id != user_id:
            await callback.answer("Плейлист не найден", show_alert=True)
            return
        
        track_count = len(playlist.track_associations) if playlist.track_associations else 0
        playlist_name = playlist.name
    
    await callback.message.edit_text(
        f"🗑 <b>Удалить плейлист?</b>\n\n"
        f"📁 «{playlist_name}»\n"
        f"🎵 {track_count} треков\n\n"
        "⚠️ Треки останутся в библиотеке,\n"
        "удалится только плейлист.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Да, удалить",
                    callback_data=f"pl:delete:{playlist_id}"
                ),
                InlineKeyboardButton(
                    text="✗ Отмена",
                    callback_data=f"pl:menu:{playlist_id}"
                )
            ]
        ])
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pl:delete:"))
async def handle_playlist_delete(callback: CallbackQuery):
    """Delete playlist"""
    playlist_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id
    
    async with get_session() as session:
        playlist = await session.get(Playlist, playlist_id)
        
        if not playlist or playlist.user_id != user_id:
            await callback.answer("Плейлист не найден", show_alert=True)
            return
        
        playlist_name = playlist.name
        await session.delete(playlist)
    
    await callback.message.edit_text(
        f"✅ Плейлист «{playlist_name}» удалён.\n\n"
        "Треки остались в библиотеке.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="◀️ К плейлистам",
                callback_data="pl:back_to_list"
            )]
        ])
    )
    await callback.answer("Удалено!")


@router.callback_query(F.data == "pl:back_to_list")
async def handle_back_to_playlist_list(callback: CallbackQuery):
    """Return to playlist list"""
    user_id = callback.from_user.id
    
    async with get_session() as session:
        result = await session.execute(
            select(Playlist)
            .options(selectinload(Playlist.track_associations))
            .where(Playlist.user_id == user_id)
            .order_by(Playlist.created_at.desc())
        )
        playlists = result.scalars().all()
        
        # Build data while session is open
        playlist_data = []
        for pl in playlists[:20]:
            track_count = len(pl.track_associations) if pl.track_associations else 0
            playlist_data.append({
                'id': pl.id,
                'name': pl.name,
                'track_count': track_count
            })
    
    if not playlist_data:
        await callback.message.edit_text(
            "📁 <b>Мои плейлисты</b>\n\n"
            "У тебя пока нет плейлистов.\n\n"
            "<b>Как создать?</b>\n"
            "• /playlist — интерактивное создание\n"
            '• /playlist "Название" — быстрое создание'
        )
        await callback.answer()
        return
    
    text = "📁 <b>Мои плейлисты</b>\n\n"
    keyboard = []
    
    for pl in playlist_data:
        text += f"• <b>{pl['name']}</b> — {pl['track_count']} 🎵\n"
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"📁 {pl['name']}",
                callback_data=f"pl:menu:{pl['id']}"
            )
        ])
    
    text += (
        "\n<b>Управление:</b> нажми на плейлист\n\n"
        "<b>Создать новый:</b>\n"
        "• /playlist — с указанием названия\n"
        '• /playlist "Имя" — быстро'
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()

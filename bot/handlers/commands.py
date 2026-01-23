"""
TG Player Bot - Command Handlers
"""
import re
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, func

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.config import get_settings
from shared.database import get_session
from shared.models import User, Track, Playlist

from services.session import session_manager


router = Router()
settings = get_settings()


class PlaylistStates(StatesGroup):
    """FSM states for playlist creation"""
    waiting_for_name = State()
    waiting_for_rename = State()  # For renaming playlist


def get_webapp_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with Mini App button"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎵 Открыть плеер",
            web_app=WebAppInfo(url=settings.webapp_url)
        )]
    ])


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command"""
    user = message.from_user
    
    async with get_session() as session:
        # Get or create user
        db_user = await session.get(User, user.id)
        
        if not db_user:
            db_user = User(
                id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )
            session.add(db_user)
        else:
            # Update user info
            db_user.username = user.username
            db_user.first_name = user.first_name
            db_user.last_name = user.last_name
    
    await message.answer(
        f"👋 Привет, <b>{user.first_name}</b>!\n\n"
        "🎵 <b>TG Player</b> — твоя музыкальная библиотека в Telegram.\n\n"
        "📤 <b>Отправь мне аудиофайл</b> — я добавлю его в твою библиотеку.\n\n"
        "📂 Нажми кнопку ниже, чтобы открыть плеер:",
        reply_markup=get_webapp_keyboard()
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    await message.answer(
        "🎵 <b>TG Player — Справка</b>\n\n"
        "<b>Как добавить музыку?</b>\n"
        "Просто отправь мне аудиофайл (MP3, FLAC, и др.) — "
        "я автоматически добавлю его в твою библиотеку.\n\n"
        "<b>Команды:</b>\n"
        "/start — Начало работы\n"
        "/help — Эта справка\n"
        "/library — Открыть плеер\n"
        "/stats — Статистика библиотеки\n"
        '/playlist — Создать плейлист\n'
        '/playlists — Мои плейлисты\n\n'
        "<b>Создание плейлиста:</b>\n"
        "1. Введи /playlist или /playlist \"Имя\"\n"
        "2. Отправь аудиофайлы\n"
        "3. Нажми «Завершить»\n\n"
        "<b>Управление плейлистами:</b>\n"
        "/playlists — список с кнопками\n"
        "• Переименовать\n"
        "• Удалить\n\n"
        "<b>Возможности плеера:</b>\n"
        "• Очереди воспроизведения\n"
        "• Поиск по артисту, названию\n"
        "• История прослушивания",
        reply_markup=get_webapp_keyboard()
    )


@router.message(Command("library"))
async def cmd_library(message: Message):
    """Handle /library command - open Mini App"""
    await message.answer(
        "🎵 Нажми кнопку, чтобы открыть плеер:",
        reply_markup=get_webapp_keyboard()
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Handle /stats command"""
    user_id = message.from_user.id
    
    async with get_session() as session:
        # Count tracks
        tracks_count = await session.scalar(
            select(func.count(Track.id)).where(Track.user_id == user_id)
        )
        
        # Count playlists
        playlists_count = await session.scalar(
            select(func.count(Playlist.id)).where(Playlist.user_id == user_id)
        )
        
        # Total duration
        total_duration = await session.scalar(
            select(func.sum(Track.duration)).where(Track.user_id == user_id)
        ) or 0
        
        # Format duration
        hours = total_duration // 3600
        minutes = (total_duration % 3600) // 60
    
    await message.answer(
        "📊 <b>Статистика библиотеки</b>\n\n"
        f"🎵 Треков: <b>{tracks_count or 0}</b>\n"
        f"📁 Плейлистов: <b>{playlists_count or 0}</b>\n"
        f"⏱ Общая длительность: <b>{hours}ч {minutes}мин</b>",
        reply_markup=get_webapp_keyboard()
    )


@router.message(Command("playlist", "плейлист"))
async def cmd_playlist(message: Message, state: FSMContext):
    """
    Handle /playlist command
    Usage: /playlist or /playlist "Название плейлиста"
    Also: /плейлист (Russian alias)
    """
    user_id = message.from_user.id
    
    # Check if already in playlist mode
    if session_manager.has_playlist_session(user_id):
        session = session_manager.get_playlist_session(user_id)
        await message.answer(
            f"⚠️ Ты уже создаёшь плейлист «{session.name}»\n"
            f"Добавлено треков: {session.track_count}\n\n"
            "Отправь ещё аудио или заверши создание.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"✓ Завершить ({session.track_count} треков)",
                        callback_data="playlist:finish"
                    ),
                    InlineKeyboardButton(
                        text="✗ Отменить",
                        callback_data="playlist:cancel"
                    )
                ]
            ])
        )
        return
    
    # Parse playlist name from command
    text = message.text or ""
    # Match /playlist "Name" or /playlist 'Name' or /плейлист "Name"
    match = re.search(r'/(?:playlist|плейлист)\s+["\'](.+?)["\']', text) or \
            re.search(r'/(?:playlist|плейлист)\s+(.+)', text)
    
    if match:
        # Name provided directly
        playlist_name = match.group(1).strip()
        if playlist_name:
            session_manager.start_playlist_session(user_id, playlist_name)
            await message.answer(
                f"📁 Плейлист «<b>{playlist_name}</b>» создаётся!\n\n"
                "🎵 Отправляй аудиофайлы — я добавлю их в плейлист.\n"
                "Когда закончишь, нажми кнопку ниже.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="✗ Отменить создание",
                        callback_data="playlist:cancel"
                    )]
                ])
            )
            return
    
    # No name provided - ask for it
    await state.set_state(PlaylistStates.waiting_for_name)
    await message.answer(
        "📁 <b>Создание плейлиста</b>\n\n"
        "Введи название для нового плейлиста:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✗ Отмена",
                callback_data="playlist:cancel_input"
            )]
        ])
    )


@router.message(PlaylistStates.waiting_for_name)
async def process_playlist_name(message: Message, state: FSMContext):
    """Process playlist name input"""
    user_id = message.from_user.id
    playlist_name = message.text.strip() if message.text else ""
    
    if not playlist_name:
        await message.answer("❌ Название не может быть пустым. Попробуй ещё раз:")
        return
    
    if len(playlist_name) > 100:
        await message.answer("❌ Название слишком длинное (макс. 100 символов). Попробуй короче:")
        return
    
    # Clear state and start session
    await state.clear()
    session_manager.start_playlist_session(user_id, playlist_name)
    
    await message.answer(
        f"✅ Плейлист «<b>{playlist_name}</b>» создаётся!\n\n"
        "🎵 Теперь отправляй аудиофайлы — я добавлю их в плейлист.\n"
        "Когда закончишь, нажми кнопку «Завершить».",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✗ Отменить создание",
                callback_data="playlist:cancel"
            )]
        ])
    )


@router.message(Command("playlists", "плейлисты"))
async def cmd_playlists(message: Message):
    """
    Handle /playlists command - show user's playlists with management options
    """
    user_id = message.from_user.id
    
    async with get_session() as session:
        # Get user's playlists
        result = await session.execute(
            select(Playlist)
            .where(Playlist.user_id == user_id)
            .order_by(Playlist.created_at.desc())
        )
        playlists = result.scalars().all()
    
    if not playlists:
        await message.answer(
            "📁 <b>Мои плейлисты</b>\n\n"
            "У тебя пока нет плейлистов.\n\n"
            "<b>Как создать?</b>\n"
            "• /playlist — интерактивное создание\n"
            '• /playlist "Название" — быстрое создание\n\n'
            "После команды отправляй аудиофайлы,\n"
            "затем нажми «Завершить»."
        )
        return
    
    # Build playlist list with inline buttons
    text = "📁 <b>Мои плейлисты</b>\n\n"
    keyboard = []
    
    for pl in playlists[:20]:  # Limit to 20 playlists
        # Count tracks
        track_count = len(pl.track_associations) if pl.track_associations else 0
        text += f"• <b>{pl.name}</b> — {track_count} 🎵\n"
        
        # Row: [Playlist name button]
        keyboard.append([
            InlineKeyboardButton(
                text=f"📁 {pl.name}",
                callback_data=f"pl:menu:{pl.id}"
            )
        ])
    
    # Add info about creation
    text += (
        "\n<b>Управление:</b> нажми на плейлист\n\n"
        "<b>Создать новый:</b>\n"
        "• /playlist — с указанием названия\n"
        '• /playlist "Имя" — быстро'
    )
    
    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@router.message(PlaylistStates.waiting_for_rename)
async def process_playlist_rename(message: Message, state: FSMContext):
    """Process playlist rename input"""
    new_name = message.text.strip() if message.text else ""
    
    if not new_name:
        await message.answer("❌ Название не может быть пустым. Попробуй ещё раз:")
        return
    
    if len(new_name) > 100:
        await message.answer("❌ Название слишком длинное (макс. 100 символов):")
        return
    
    # Get playlist id from state
    data = await state.get_data()
    playlist_id = data.get("rename_playlist_id")
    
    if not playlist_id:
        await state.clear()
        await message.answer("❌ Ошибка. Попробуй снова через /playlists")
        return
    
    # Update in database
    async with get_session() as session:
        playlist = await session.get(Playlist, playlist_id)
        if playlist and playlist.user_id == message.from_user.id:
            old_name = playlist.name
            playlist.name = new_name
            await message.answer(
                f"✅ Плейлист переименован!\n\n"
                f"«{old_name}» → «<b>{new_name}</b>»",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="◀️ К плейлистам",
                        callback_data="pl:back_to_list"
                    )]
                ])
            )
        else:
            await message.answer("❌ Плейлист не найден.")
    
    await state.clear()

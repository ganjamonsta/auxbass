"""
TG Player Bot - Command Handlers v2

Uses new modular service architecture.
"""
import re
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.config import get_settings
from shared.database import get_session
from shared.models import User, Playlist

from bot.services import track_service, channel_service
from bot.services.session import session_manager
from bot.handlers.keyboards import (
    get_webapp_keyboard,
    get_stats_keyboard,
    get_channel_setup_keyboard,
    get_cancel_keyboard,
    get_help_menu_keyboard,
)


router = Router()
settings = get_settings()


class PlaylistStates(StatesGroup):
    """FSM states for playlist creation"""
    waiting_for_name = State()
    waiting_for_rename = State()


class ChannelStates(StatesGroup):
    """FSM states for channel setup"""
    waiting_for_channel = State()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command"""
    user = message.from_user
    
    async with get_session() as session:
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
            db_user.username = user.username
            db_user.first_name = user.first_name
            db_user.last_name = user.last_name
    
    await message.answer(
        f"👋 Привет, <b>{user.first_name}</b>!\n\n"
        "🎵 <b>TG Player</b> — твоя музыкальная библиотека в Telegram.\n\n"
        "📤 <b>Отправь мне аудиофайл</b> — я добавлю его в твою библиотеку.\n\n"
        "✨ <b>Возможности:</b>\n"
        "• Автоматическое обогащение метаданных (Deezer/Last.fm)\n"
        "• Группировка по альбомам и исполнителям\n"
        "• Создание плейлистов\n"
        "• Бекап библиотеки в личный канал\n\n"
        "📂 Нажми кнопку ниже, чтобы открыть плеер:",
        reply_markup=get_webapp_keyboard()
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command - show main help menu with sections"""
    await message.answer(
        "🎵 <b>TG Player — Центр помощи</b>\n\n"
        "Добро пожаловать в твою персональную музыкальную библиотеку!\n\n"
        "<b>🚀 Быстрый старт:</b>\n"
        "Просто отправь аудиофайл — всё остальное бот сделает сам.\n\n"
        "Выбери раздел, чтобы узнать больше:",
        reply_markup=get_help_menu_keyboard()
    )


@router.message(Command("library"))
async def cmd_library(message: Message):
    """Handle /library command - open Mini App"""
    await message.answer(
        "🎵 Нажми кнопку, чтобы открыть плеер:",
        reply_markup=get_webapp_keyboard()
    )


@router.message(Command("login", "code", "web"))
async def cmd_login(message: Message):
    """Handle /login command - generate auth code for browser login"""
    import aiohttp
    
    user = message.from_user
    
    try:
        async with aiohttp.ClientSession() as http_session:
            async with http_session.post(
                f"{settings.api_url}/api/auth/generate-code",
                params={
                    "user_id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name or "",
                    "username": user.username or "",
                },
                headers={"X-Bot-Secret": settings.secret_key},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    code = data["code"]
                    expires_in = data["expires_in"] // 60
                    
                    await message.answer(
                        f"🔐 <b>Код для входа в браузере:</b>\n\n"
                        f"<code>{code}</code>\n\n"
                        f"⏱ Код действителен {expires_in} минут.\n\n"
                        f"🌐 Откройте <b>{settings.webapp_url}</b> в браузере "
                        f"и введите этот код."
                    )
                else:
                    await message.answer(
                        "❌ Не удалось получить код. Попробуйте позже."
                    )
    except Exception as e:
        await message.answer(
            "❌ Ошибка подключения к серверу. Попробуйте позже."
        )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Handle /stats command"""
    from bot.handlers.helpers import format_stats_text
    
    text = await format_stats_text(message.from_user.id)
    await message.answer(text, reply_markup=get_stats_keyboard())


@router.message(Command("channel"))
async def cmd_channel(message: Message, state: FSMContext):
    """Handle /channel command - setup backup channel"""
    user_id = message.from_user.id
    
    # Check if user already has a channel
    channel = await channel_service.get_user_channel(user_id)
    
    if channel:
        from bot.handlers.keyboards import get_channel_keyboard
        await message.answer(
            f"☁️ <b>Ваш канал для бекапа</b>\n\n"
            f"📢 {channel.channel_title or 'Канал'}\n"
            f"🎵 Сохранено треков: {getattr(channel, '_message_count', 0)}",
            reply_markup=get_channel_keyboard(channel.channel_id, channel.channel_username)
        )
        return
    
    bot_info = await message.bot.get_me()
    await message.answer(
        "☁️ <b>Настройка канала для бекапа</b>\n\n"
        "Создайте приватный канал в Telegram и добавьте меня администратором.\n\n"
        "<b>Инструкция:</b>\n"
        "1. Создайте новый канал (приватный)\n"
        f"2. Добавьте @{bot_info.username} как администратора\n"
        "3. Дайте права на публикацию сообщений\n"
        "4. Перешлите мне любое сообщение из канала\n\n"
        "Все новые треки будут автоматически сохраняться в ваш канал с хэштегами.",
        reply_markup=get_channel_setup_keyboard()
    )
    
    await state.set_state(ChannelStates.waiting_for_channel)


@router.message(ChannelStates.waiting_for_channel)
async def process_channel_forward(message: Message, state: FSMContext):
    """Process forwarded message from user's channel"""
    if not message.forward_from_chat:
        await message.answer(
            "❌ Пожалуйста, перешлите сообщение из вашего канала.\n\n"
            "Убедитесь, что бот добавлен как администратор.",
            reply_markup=get_cancel_keyboard("channel:cancel")
        )
        return
    
    chat = message.forward_from_chat
    if chat.type != "channel":
        await message.answer(
            "❌ Это не канал. Перешлите сообщение именно из канала.",
            reply_markup=get_cancel_keyboard("channel:cancel")
        )
        return
    
    # Try to setup channel
    try:
        channel = await channel_service.setup_channel(
            user_id=message.from_user.id,
            channel_id=chat.id,
            channel_username=chat.username,
            channel_title=chat.title,
            bot=message.bot,
        )
        
        if channel:
            await state.clear()
            await message.answer(
                f"✅ <b>Канал подключён!</b>\n\n"
                f"📢 {chat.title}\n\n"
                "Теперь все новые треки будут автоматически сохраняться в ваш канал с хэштегами.",
            )
        else:
            await message.answer(
                "❌ Не удалось подключить канал.\n\n"
                "Убедитесь, что бот имеет права администратора "
                "и может публиковать сообщения.",
                reply_markup=get_channel_setup_keyboard()
            )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\n"
            "Попробуйте ещё раз или обратитесь в поддержку.",
            reply_markup=get_channel_setup_keyboard()
        )


@router.message(Command("sync"))
async def cmd_sync(message: Message):
    """Handle /sync command - sync library to channel"""
    user_id = message.from_user.id
    
    channel = await channel_service.get_user_channel(user_id)
    if not channel:
        await message.answer(
            "❌ У вас не настроен канал для бекапа.\n\n"
            "Используйте /channel для настройки."
        )
        return
    
    # Check if sync is already running
    if channel_service.is_sync_active(user_id):
        sync_status = channel_service.get_sync_status(user_id)
        await message.answer(
            f"🔄 <b>Синхронизация уже идёт!</b>\n\n"
            f"⏳ Отправлено: {sync_status['synced']}/{sync_status['total']}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="⛔ Прервать",
                    callback_data="channel:sync_cancel"
                )]
            ])
        )
        return
    
    # Get sync stats first
    stats = await channel_service.get_sync_stats(user_id)
    
    if stats.get("error"):
        await message.answer(f"❌ {stats['error']}")
        return
    
    if stats["to_sync"] == 0:
        # All synced, but check for incomplete hashtags
        status_msg = await message.answer(
            f"✅ <b>Все треки уже синхронизированы!</b>\n\n"
            f"📢 {stats['channel_title']}\n"
            f"🎵 В канале: <b>{stats['already_synced']}</b> треков\n"
            f"📚 В библиотеке: <b>{stats['total_tracks']}</b> треков\n\n"
            f"🔍 Проверяю хештеги..."
        )
        
        # Progress callback for hashtag updates
        async def hashtag_progress(current, total, updated):
            try:
                progress_text = f"🔍 Обновляю хештеги... {updated}"
                if current < total:
                    progress_text += f" (проверено {current}/{total})"
                await status_msg.edit_text(
                    f"✅ <b>Все треки уже синхронизированы!</b>\n\n"
                    f"📢 {stats['channel_title']}\n"
                    f"🎵 В канале: <b>{stats['already_synced']}</b> треков\n"
                    f"📚 В библиотеке: <b>{stats['total_tracks']}</b> треков\n\n"
                    f"{progress_text}"
                )
            except:
                pass
        
        # Update incomplete hashtags
        update_result = await channel_service.update_incomplete_messages(
            user_id=user_id,
            bot=message.bot,
            progress_callback=hashtag_progress,
        )
        
        if update_result["updated"] > 0:
            await status_msg.edit_text(
                f"✅ <b>Синхронизация завершена!</b>\n\n"
                f"📢 {stats['channel_title']}\n"
                f"🎵 В канале: <b>{stats['already_synced']}</b> треков\n\n"
                f"🏷️ Обновлено хештегов: <b>{update_result['updated']}</b>\n"
                f"📊 Проверено: <b>{update_result['checked']}</b>"
            )
        else:
            await status_msg.edit_text(
                f"✅ <b>Всё актуально!</b>\n\n"
                f"📢 {stats['channel_title']}\n"
                f"🎵 В канале: <b>{stats['already_synced']}</b> треков\n"
                f"📊 Проверено: <b>{update_result['checked']}</b>\n\n"
                f"Все хештеги уже обновлены."
            )
        return
    
    status_msg = await message.answer(
        f"🔄 <b>Синхронизация...</b>\n\n"
        f"📢 {stats['channel_title']}\n"
        f"📤 К отправке: <b>{stats['to_sync']}</b> треков\n\n"
        f"⏳ Отправлено: 0/{stats['to_sync']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="⛔ Прервать",
                callback_data="channel:sync_cancel"
            )]
        ])
    )
    
    # Progress callback - update on every track
    channel_title = stats['channel_title']
    to_sync_total = stats['to_sync']
    
    async def progress_callback(current, total, synced):
        try:
            await status_msg.edit_text(
                f"🔄 <b>Синхронизация...</b>\n\n"
                f"📢 {channel_title}\n"
                f"📤 К отправке: <b>{total}</b> треков\n\n"
                f"⏳ Отправлено: {synced}/{total}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="⛔ Прервать",
                        callback_data="channel:sync_cancel"
                    )]
                ])
            )
        except:
            pass
    
    result = await channel_service.sync_all_tracks(
        user_id=user_id,
        bot=message.bot,
        progress_callback=progress_callback
    )
    
    if result.get("error"):
        await status_msg.edit_text(
            f"❌ Ошибка синхронизации: {result['error']}"
        )
        return
    
    if result.get("cancelled"):
        await status_msg.edit_text(
            f"⛔ <b>Синхронизация прервана</b>\n\n"
            f"📤 Успешно отправлено: <b>{result['synced']}</b>\n"
            f"⏭️ Уже было в канале: <b>{result['skipped']}</b>"
        )
        return
    
    # Sync completed, now update incomplete hashtags
    synced_count = result['synced']
    skipped_count = result['skipped']
    
    await status_msg.edit_text(
        f"✅ <b>Треки отправлены!</b>\n\n"
        f"📤 Добавлено в канал: <b>{synced_count}</b>\n"
        f"⏭️ Уже было в канале: <b>{skipped_count}</b>\n\n"
        f"🔍 Проверяю хештеги..."
    )
    
    # Progress callback for hashtag updates after sync
    async def hashtag_progress_after_sync(current, total, updated):
        try:
            progress_text = f"🔍 Обновляю хештеги... {updated}"
            if current < total:
                progress_text += f" (проверено {current}/{total})"
            await status_msg.edit_text(
                f"✅ <b>Треки отправлены!</b>\n\n"
                f"📤 Добавлено в канал: <b>{synced_count}</b>\n"
                f"⏭️ Уже было в канале: <b>{skipped_count}</b>\n\n"
                f"{progress_text}"
            )
        except:
            pass
    
    update_result = await channel_service.update_incomplete_messages(
        user_id=user_id,
        bot=message.bot,
        progress_callback=hashtag_progress_after_sync,
    )
    
    # Final result message
    hashtag_note = ""
    if update_result["updated"] > 0:
        hashtag_note = f"\n🏷️ Обновлено хештегов: <b>{update_result['updated']}</b>"
    
    await status_msg.edit_text(
        f"✅ <b>Синхронизация завершена!</b>\n\n"
        f"📤 Добавлено в канал: <b>{result['synced']}</b>\n"
        f"⏭️ Уже было в канале: <b>{result['skipped']}</b>\n"
        f"❌ Ошибок: <b>{result['failed']}</b>\n"
        f"📊 Всего треков: <b>{result['total']}</b>{hashtag_note}"
    )


@router.message(Command("playlist", "плейлист"))
async def cmd_playlist(message: Message, state: FSMContext):
    """Handle /playlist command"""
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
    match = re.search(r'/(?:playlist|плейлист)\s+["\'](.+?)["\']', text) or \
            re.search(r'/(?:playlist|плейлист)\s+(.+)', text)
    
    if match:
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
        await message.answer("❌ Название слишком длинное (макс. 100 символов):")
        return
    
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
    """Handle /playlists command"""
    from bot.handlers.helpers import get_playlist_list_data, format_playlist_list
    
    playlist_data = await get_playlist_list_data(message.from_user.id)
    text, keyboard = format_playlist_list(playlist_data)
    
    if keyboard is None:
        # No playlists - add creation hints
        await message.answer(text)
        return
    
    text += (
        "\n\n<b>Создать новый:</b>\n"
        "• /playlist — с указанием названия\n"
        '• /playlist "Имя" — быстро'
    )
    
    await message.answer(text, reply_markup=keyboard)


@router.message(PlaylistStates.waiting_for_rename)
async def process_playlist_rename(message: Message, state: FSMContext):
    """Process playlist rename input"""
    new_name = message.text.strip() if message.text else ""
    
    if not new_name:
        await message.answer("❌ Название не может быть пустым:")
        return
    
    if len(new_name) > 100:
        await message.answer("❌ Название слишком длинное (макс. 100 символов):")
        return
    
    data = await state.get_data()
    playlist_id = data.get("rename_playlist_id")
    
    if not playlist_id:
        await state.clear()
        await message.answer("❌ Ошибка. Попробуй снова через /playlists")
        return
    
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

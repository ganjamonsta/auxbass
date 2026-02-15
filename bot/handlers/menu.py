"""
TG Player Bot - Unified Hierarchical Menu

Single router that handles:
  • Main menu (menu:*)
  • Library section (lib:*)
  • Playlists section (pl:*)  — creation FSM lives here too
  • Channel section (ch:*)     — setup FSM lives here too
  • Statistics section (stats:*)

Old commands (/library, /channel, /stats, /playlists, /sync, /duplicates)
are rewritten as thin aliases that just open the corresponding menu section.
"""
import re
import logging
from typing import Optional

from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from shared.config import get_settings
from shared.database import get_session
from shared.models import (
    User,
    Playlist,
    PlaylistTrack,
    UserLibrary,
    Track,
    ChannelMessage,
    ChannelMessageStatus,
    UserChannel,
    Album,
    AlbumTrack,
)

from bot.services import track_service, channel_service
from bot.services.session import session_manager
from bot.handlers.menu_keyboards import (
    get_main_menu_keyboard,
    get_library_keyboard,
    get_playlists_keyboard,
    get_playlists_empty_keyboard,
    get_playlist_detail_keyboard,
    get_playlist_delete_confirm_keyboard,
    get_playlist_create_cancel_keyboard,
    get_playlist_building_keyboard,
    get_channel_not_connected_keyboard,
    get_channel_main_keyboard,
    get_channel_settings_keyboard,
    get_channel_disconnect_confirm_keyboard,
    get_channel_setup_waiting_keyboard,
    get_channel_reset_confirm_keyboard,
    get_channel_operation_keyboard,
    get_channel_back_keyboard,
    get_stats_menu_keyboard,
)

router = Router()
settings = get_settings()
logger = logging.getLogger(__name__)


# ───────────────────────── FSM States ─────────────────────────

class MenuStates(StatesGroup):
    """FSM states for all menu interactions"""
    # Playlist creation
    playlist_waiting_name = State()
    playlist_waiting_rename = State()
    # Channel setup
    channel_waiting_forward = State()


# ───────────────────────── Helpers ─────────────────────────

async def _get_library_text(user_id: int) -> tuple[str, int]:
    """Build library section text. Returns (text, track_count)."""
    stats = await track_service.get_library_stats(user_id)
    total = stats["total_tracks"]
    albums = stats["album_count"]
    dur_sec = stats.get("total_duration_seconds", 0)
    hours = dur_sec // 3600
    minutes = (dur_sec % 3600) // 60

    text = (
        "📚 <b>Моя библиотека</b>\n\n"
        f"🎵 Треков: <b>{total}</b>\n"
        f"💿 Альбомов: <b>{albums}</b>\n"
        f"⏱ Длительность: <b>{hours}ч {minutes}мин</b>\n\n"
        "Открой плеер, чтобы слушать, управлять лайками и избранным."
    )
    return text, total


async def _get_playlists_data(user_id: int) -> list[dict]:
    """Fetch playlists for user."""
    async with get_session() as session:
        result = await session.execute(
            select(Playlist)
            .options(selectinload(Playlist.tracks))
            .where(Playlist.owner_id == user_id)
            .order_by(Playlist.created_at.desc())
        )
        playlists = result.scalars().all()
        return [
            {
                "id": pl.id,
                "name": pl.name,
                "track_count": len(pl.tracks) if pl.tracks else 0,
            }
            for pl in playlists[:20]
        ]


async def _get_channel_status_text(user_id: int) -> tuple[str, Optional[object]]:
    """Build channel section text. Returns (text, channel_or_None)."""
    channel = await channel_service.get_user_channel(user_id)
    if not channel:
        return (
            "☁️ <b>Мой канал</b>\n\n"
            "Канал не подключён.\n\n"
            "Канал — это ваше хранилище аудио в Telegram.\n"
            "Все треки автоматически пересылаются туда с хэштегами."
        ), None

    # Counts by status
    async with get_session() as session:
        rows = (
            await session.execute(
                select(ChannelMessage.status, func.count(ChannelMessage.id))
                .where(ChannelMessage.channel_id == channel.id)
                .group_by(ChannelMessage.status)
            )
        ).all()

    counts = {s: c for s, c in rows}
    sent = counts.get(ChannelMessageStatus.SENT, 0) + counts.get("sent", 0)
    pending = counts.get(ChannelMessageStatus.PENDING, 0) + counts.get("pending", 0)
    failed = counts.get(ChannelMessageStatus.FAILED, 0) + counts.get("failed", 0)

    total_tracks = sent + pending + failed

    status_lines = [
        f"☁️ <b>Мой канал</b>\n",
        f"📢 {channel.channel_title or 'Канал'}",
        f"✅ Подключён\n",
        f"🎵 Треков в канале: <b>{sent}</b>",
    ]
    if pending:
        status_lines.append(f"⏳ Ожидают отправки: <b>{pending}</b>")
    if failed:
        status_lines.append(f"❌ Ошибки отправки: <b>{failed}</b>")

    return "\n".join(status_lines), channel


async def _get_stats_text(user_id: int) -> str:
    """Build detailed statistics text including channel info."""
    stats = await track_service.get_library_stats(user_id)

    total = stats["total_tracks"]
    albums = stats["album_count"]
    dur_sec = stats.get("total_duration_seconds", 0)
    hours = dur_sec // 3600
    minutes = (dur_sec % 3600) // 60

    enrichment = stats.get("enrichment", {})
    pending_enrich = enrichment.get("pending", 0)
    failed_enrich = enrichment.get("failed", 0)

    # Artist count
    async with get_session() as session:
        artist_count = (
            await session.scalar(
                select(func.count(func.distinct(Track.normalized_artist)))
                .join(UserLibrary, UserLibrary.track_id == Track.id)
                .where(
                    UserLibrary.user_id == user_id,
                    Track.normalized_artist.isnot(None),
                    Track.normalized_artist != "",
                )
            )
        ) or 0

    # Channel stats
    channel = await channel_service.get_user_channel(user_id)
    channel_text = ""
    if channel:
        async with get_session() as session:
            rows = (
                await session.execute(
                    select(ChannelMessage.status, func.count(ChannelMessage.id))
                    .where(ChannelMessage.channel_id == channel.id)
                    .group_by(ChannelMessage.status)
                )
            ).all()
        counts = {s: c for s, c in rows}
        ch_sent = counts.get(ChannelMessageStatus.SENT, 0) + counts.get("sent", 0)
        ch_pending = counts.get(ChannelMessageStatus.PENDING, 0) + counts.get("pending", 0)
        ch_failed = counts.get(ChannelMessageStatus.FAILED, 0) + counts.get("failed", 0)
        channel_text = (
            f"\n\n<b>☁️ Канал ({channel.channel_title or 'Канал'}):</b>\n"
            f"✅ Отправлено: <b>{ch_sent}</b>\n"
            f"⏳ Pending: <b>{ch_pending}</b>\n"
            f"❌ Failed: <b>{ch_failed}</b>"
        )

    enrichment_text = ""
    if pending_enrich:
        enrichment_text = f"\n🔄 Обогащение: {pending_enrich} в очереди"
    if failed_enrich:
        enrichment_text += f"\n⚠️ Не обогащено: {failed_enrich}"

    return (
        "📊 <b>Статистика</b>\n\n"
        f"🎵 Треков: <b>{total}</b>\n"
        f"💿 Альбомов: <b>{albums}</b>\n"
        f"👤 Исполнителей: <b>{artist_count}</b>\n"
        f"⏱ Длительность: <b>{hours}ч {minutes}мин</b>"
        f"{enrichment_text}"
        f"{channel_text}"
    )


# ═══════════════════════════════════════════════════════════
#                    COMMANDS  (thin aliases)
# ═══════════════════════════════════════════════════════════

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Welcome message + register user + show main menu"""
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

    await state.clear()
    await message.answer(
        f"👋 Привет, <b>{user.first_name}</b>!\n\n"
        "🎵 <b>TG Player</b> — твоя музыкальная библиотека в Telegram.\n\n"
        "📤 Отправь мне аудиофайл — я добавлю его в библиотеку.\n\n"
        "Выбери раздел:",
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(Command("menu", "help"))
async def cmd_menu(message: Message, state: FSMContext):
    """Show main menu"""
    await state.clear()
    await message.answer(
        "🎵 <b>TG Player — Главное меню</b>\n\n"
        "Выбери раздел:",
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(Command("library"))
async def cmd_library(message: Message, state: FSMContext):
    """Alias → Library section"""
    await state.clear()
    text, total = await _get_library_text(message.from_user.id)
    await message.answer(text, reply_markup=get_library_keyboard(total))


@router.message(Command("playlists", "playlist", "плейлисты", "плейлист"))
async def cmd_playlists(message: Message, state: FSMContext):
    """Alias → Playlists section.
    
    If command has arguments like /playlist "name", start creation directly.
    """
    text_raw = message.text or ""
    # Check for quick-create: /playlist "Name" or /playlist Name
    match = (
        re.search(r'/(?:playlist|плейлист)\s+["\'](.+?)["\']', text_raw)
        or re.search(r'/(?:playlist|плейлист)\s+(.+)', text_raw)
    )
    if match:
        name = match.group(1).strip()
        if name:
            await _start_playlist_building(message, state, name)
            return

    await state.clear()
    await _show_playlists_section(message, message.from_user.id)


@router.message(Command("channel"))
async def cmd_channel(message: Message, state: FSMContext):
    """Alias → Channel section"""
    await state.clear()
    await _show_channel_section(message, message.from_user.id)


@router.message(Command("sync"))
async def cmd_sync(message: Message, state: FSMContext):
    """Alias → Channel section (no separate sync action)"""
    await state.clear()
    await _show_channel_section(message, message.from_user.id)


@router.message(Command("stats"))
async def cmd_stats(message: Message, state: FSMContext):
    """Alias → Stats section"""
    await state.clear()
    text = await _get_stats_text(message.from_user.id)
    await message.answer(text, reply_markup=get_stats_menu_keyboard())


@router.message(Command("duplicates", "dedup"))
async def cmd_duplicates(message: Message, state: FSMContext):
    """Alias → Channel > duplicates"""
    await state.clear()
    await _show_channel_section(message, message.from_user.id)


@router.message(Command("login", "code", "web"))
async def cmd_login(message: Message):
    """Generate auth code for browser login"""
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
                timeout=aiohttp.ClientTimeout(total=10),
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
                        f"и введите этот код.",
                    )
                else:
                    await message.answer("❌ Не удалось получить код. Попробуйте позже.")
    except Exception:
        await message.answer("❌ Ошибка подключения к серверу. Попробуйте позже.")


# ═══════════════════════════════════════════════════════════
#                 MAIN MENU  callbacks
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "menu:main")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🎵 <b>TG Player — Главное меню</b>\n\nВыбери раздел:",
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════════
#                 LIBRARY  section
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "menu:library")
async def cb_library(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text, total = await _get_library_text(callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=get_library_keyboard(total))
    await callback.answer()


@router.callback_query(F.data == "lib:login")
async def cb_library_login(callback: CallbackQuery):
    """Generate login code from within the menu"""
    import aiohttp

    user = callback.from_user
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
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    code = data["code"]
                    expires_in = data["expires_in"] // 60
                    await callback.message.edit_text(
                        f"🔐 <b>Код для входа в браузере:</b>\n\n"
                        f"<code>{code}</code>\n\n"
                        f"⏱ Код действителен {expires_in} минут.\n\n"
                        f"🌐 Откройте <b>{settings.webapp_url}</b>",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="◀️ Библиотека", callback_data="menu:library")],
                        ]),
                    )
                else:
                    await callback.answer("❌ Ошибка получения кода", show_alert=True)
    except Exception:
        await callback.answer("❌ Сервер недоступен", show_alert=True)


# ═══════════════════════════════════════════════════════════
#                 PLAYLISTS  section
# ═══════════════════════════════════════════════════════════

async def _show_playlists_section(
    target: Message | CallbackQuery, user_id: int, *, edit: bool = False
):
    """Show playlists list via answer or edit_text."""
    data = await _get_playlists_data(user_id)
    if data:
        text = "🗂 <b>Плейлисты</b>\n\n"
        for pl in data:
            text += f"• <b>{pl['name']}</b> — {pl['track_count']} 🎵\n"
        kb = get_playlists_keyboard(data)
    else:
        text = (
            "🗂 <b>Плейлисты</b>\n\n"
            "У тебя пока нет плейлистов.\n"
            "Нажми кнопку ниже, чтобы создать первый!"
        )
        kb = get_playlists_empty_keyboard()

    if edit and isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=kb)
    elif isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=kb)
    else:
        await target.answer(text, reply_markup=kb)


@router.callback_query(F.data == "menu:playlists")
async def cb_playlists(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await _show_playlists_section(callback, callback.from_user.id, edit=True)
    await callback.answer()


@router.callback_query(F.data == "pl:create")
async def cb_playlist_create(callback: CallbackQuery, state: FSMContext):
    """Start playlist creation — ask for name"""
    user_id = callback.from_user.id
    if session_manager.has_playlist_session(user_id):
        session = session_manager.get_playlist_session(user_id)
        await callback.answer(
            f"Ты уже создаёшь плейлист «{session.name}»!", show_alert=True
        )
        return

    await state.set_state(MenuStates.playlist_waiting_name)
    await callback.message.edit_text(
        "🗂 <b>Создание плейлиста</b>\n\nВведи название:",
        reply_markup=get_playlist_create_cancel_keyboard(),
    )
    await callback.answer()


@router.message(MenuStates.playlist_waiting_name)
async def fsm_playlist_name(message: Message, state: FSMContext):
    """Receive playlist name from user"""
    name = (message.text or "").strip()
    if not name:
        await message.answer("❌ Название не может быть пустым. Попробуй ещё раз:")
        return
    if len(name) > 100:
        await message.answer("❌ Максимум 100 символов. Попробуй короче:")
        return

    await _start_playlist_building(message, state, name)


async def _start_playlist_building(message: Message, state: FSMContext, name: str):
    """Common helper: start playlist building session"""
    await state.clear()
    session_manager.start_playlist_session(message.from_user.id, name)
    await message.answer(
        f"✅ Плейлист «<b>{name}</b>» создаётся!\n\n"
        "🎵 Отправляй аудиофайлы — я добавлю их в плейлист.\n"
        "Когда закончишь, нажми «Завершить».",
        reply_markup=get_playlist_building_keyboard(0),
    )


@router.callback_query(F.data == "pl:cancel_input")
async def cb_playlist_cancel_input(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await _show_playlists_section(callback, callback.from_user.id, edit=True)
    await callback.answer()


@router.callback_query(F.data.startswith("pl:menu:"))
async def cb_playlist_detail(callback: CallbackQuery):
    """Show single playlist details"""
    playlist_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id

    async with get_session() as session:
        playlist = await session.get(
            Playlist, playlist_id, options=[selectinload(Playlist.tracks)]
        )
        if not playlist or playlist.owner_id != user_id:
            await callback.answer("Плейлист не найден", show_alert=True)
            return
        track_count = len(playlist.tracks) if playlist.tracks else 0
        name = playlist.name
        created = playlist.created_at.strftime("%d.%m.%Y")

    await callback.message.edit_text(
        f"📁 <b>{name}</b>\n\n"
        f"🎵 Треков: {track_count}\n"
        f"📅 Создан: {created}\n\n"
        "Выбери действие:",
        reply_markup=get_playlist_detail_keyboard(playlist_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pl:rename:"))
async def cb_playlist_rename_start(callback: CallbackQuery, state: FSMContext):
    playlist_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id

    async with get_session() as session:
        playlist = await session.get(Playlist, playlist_id)
        if not playlist or playlist.owner_id != user_id:
            await callback.answer("Плейлист не найден", show_alert=True)
            return
        name = playlist.name

    await state.set_state(MenuStates.playlist_waiting_rename)
    await state.update_data(rename_playlist_id=playlist_id)
    await callback.message.edit_text(
        f"✏️ <b>Переименование</b>\n\n"
        f"Текущее: «{name}»\nВведи новое название:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✗ Отмена", callback_data=f"pl:menu:{playlist_id}")],
        ]),
    )
    await callback.answer()


@router.message(MenuStates.playlist_waiting_rename)
async def fsm_playlist_rename(message: Message, state: FSMContext):
    new_name = (message.text or "").strip()
    if not new_name:
        await message.answer("❌ Название не может быть пустым:")
        return
    if len(new_name) > 100:
        await message.answer("❌ Слишком длинное (макс. 100):")
        return

    data = await state.get_data()
    playlist_id = data.get("rename_playlist_id")
    if not playlist_id:
        await state.clear()
        await message.answer("❌ Ошибка. Попробуй через меню.")
        return

    async with get_session() as session:
        playlist = await session.get(Playlist, playlist_id)
        if playlist and playlist.owner_id == message.from_user.id:
            old = playlist.name
            playlist.name = new_name
            await message.answer(
                f"✅ Переименовано: «{old}» → «<b>{new_name}</b>»",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Плейлисты", callback_data="menu:playlists")],
                ]),
            )
        else:
            await message.answer("❌ Плейлист не найден.")

    await state.clear()


@router.callback_query(F.data.startswith("pl:delete_confirm:"))
async def cb_playlist_delete_confirm(callback: CallbackQuery):
    playlist_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id

    async with get_session() as session:
        playlist = await session.get(
            Playlist, playlist_id, options=[selectinload(Playlist.tracks)]
        )
        if not playlist or playlist.owner_id != user_id:
            await callback.answer("Плейлист не найден", show_alert=True)
            return
        track_count = len(playlist.tracks) if playlist.tracks else 0
        name = playlist.name

    await callback.message.edit_text(
        f"🗑 <b>Удалить плейлист?</b>\n\n"
        f"📁 «{name}» — {track_count} треков\n"
        "⚠️ Треки останутся в библиотеке.",
        reply_markup=get_playlist_delete_confirm_keyboard(playlist_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pl:delete:"))
async def cb_playlist_delete(callback: CallbackQuery):
    playlist_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id

    async with get_session() as session:
        playlist = await session.get(Playlist, playlist_id)
        if not playlist or playlist.owner_id != user_id:
            await callback.answer("Плейлист не найден", show_alert=True)
            return
        name = playlist.name
        await session.delete(playlist)

    await callback.message.edit_text(
        f"✅ Плейлист «{name}» удалён.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Плейлисты", callback_data="menu:playlists")],
        ]),
    )
    await callback.answer("Удалено!")


# Keep old playlist creation callbacks compatible (from audio.py flow)
@router.callback_query(F.data == "playlist:finish")
async def cb_playlist_finish(callback: CallbackQuery):
    """Finish playlist building and save"""
    user_id = callback.from_user.id
    ps = session_manager.get_playlist_session(user_id)
    if not ps:
        await callback.answer("Нет активного плейлиста", show_alert=True)
        return
    if ps.track_count == 0:
        await callback.answer("Добавь хотя бы один трек!", show_alert=True)
        return

    async with get_session() as session:
        playlist = Playlist(owner_id=user_id, name=ps.name, is_public=True)
        session.add(playlist)
        await session.flush()
        for pos, tid in enumerate(ps.track_ids):
            session.add(PlaylistTrack(playlist_id=playlist.id, track_id=tid, position=pos))

    session_manager.end_playlist_session(user_id)
    await callback.message.edit_text(
        f"🎉 <b>Плейлист создан!</b>\n\n"
        f"📁 «{ps.name}» — {ps.track_count} треков",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Плейлисты", callback_data="menu:playlists")],
        ]),
    )
    await callback.answer("Плейлист создан!")


@router.callback_query(F.data == "playlist:cancel")
async def cb_playlist_cancel(callback: CallbackQuery):
    user_id = callback.from_user.id
    ps = session_manager.get_playlist_session(user_id)
    if ps:
        session_manager.end_playlist_session(user_id)
        await callback.message.edit_text(f"❌ Плейлист «{ps.name}» отменён.")
    else:
        await callback.message.edit_text("❌ Отменено.")
    await callback.answer()


@router.callback_query(F.data.startswith("playlist:add_existing:"))
async def cb_add_existing_to_playlist(callback: CallbackQuery):
    user_id = callback.from_user.id
    track_id = int(callback.data.split(":")[2])
    ps = session_manager.get_playlist_session(user_id)
    if not ps:
        await callback.answer("Нет активного плейлиста", show_alert=True)
        return
    if track_id in ps.track_ids:
        await callback.answer("Уже в плейлисте!", show_alert=True)
        return
    ps.add_track(track_id)
    await callback.message.edit_text(
        f"✅ Добавлено в «{ps.name}» ({ps.track_count} треков)",
        reply_markup=get_playlist_building_keyboard(ps.track_count),
    )
    await callback.answer("Добавлено!")


@router.callback_query(F.data == "playlist:skip_duplicate")
async def cb_skip_duplicate(callback: CallbackQuery):
    user_id = callback.from_user.id
    ps = session_manager.get_playlist_session(user_id)
    if ps:
        await callback.message.edit_text(
            f"⏭ Пропущено. Плейлист «{ps.name}» — {ps.track_count} треков",
            reply_markup=get_playlist_building_keyboard(ps.track_count),
        )
    else:
        await callback.message.edit_text("⏭ Пропущено.")
    await callback.answer()


@router.callback_query(F.data == "pl:back_to_list")
async def cb_back_to_playlist_list(callback: CallbackQuery):
    await _show_playlists_section(callback, callback.from_user.id, edit=True)
    await callback.answer()


# ═══════════════════════════════════════════════════════════
#                 CHANNEL  section
# ═══════════════════════════════════════════════════════════

async def _show_channel_section(
    target: Message | CallbackQuery, user_id: int, *, edit: bool = False
):
    text, channel = await _get_channel_status_text(user_id)
    if channel:
        kb = get_channel_main_keyboard(channel.channel_username)
    else:
        kb = get_channel_not_connected_keyboard()

    if edit and isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=kb)
    elif isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=kb)
    else:
        await target.answer(text, reply_markup=kb)


@router.callback_query(F.data == "menu:channel")
async def cb_channel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await _show_channel_section(callback, callback.from_user.id, edit=True)
    await callback.answer()


# ---- Channel Setup ----

@router.callback_query(F.data == "ch:setup")
async def cb_channel_setup(callback: CallbackQuery, state: FSMContext):
    bot_info = await callback.bot.get_me()
    await state.set_state(MenuStates.channel_waiting_forward)
    await callback.message.edit_text(
        "🔗 <b>Подключение канала</b>\n\n"
        "1. Создайте приватный канал\n"
        f"2. Добавьте @{bot_info.username} администратором\n"
        "3. Дайте права на публикацию сообщений\n"
        "4. Перешлите мне любое сообщение из канала",
        reply_markup=get_channel_setup_waiting_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "ch:setup_cancel")
async def cb_channel_setup_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await _show_channel_section(callback, callback.from_user.id, edit=True)
    await callback.answer()


@router.message(MenuStates.channel_waiting_forward)
async def fsm_channel_forward(message: Message, state: FSMContext):
    """Receive forwarded message from user's channel"""
    if not message.forward_from_chat:
        await message.answer(
            "❌ Перешлите сообщение из канала.\n"
            "Убедитесь, что бот — администратор.",
            reply_markup=get_channel_setup_waiting_keyboard(),
        )
        return

    chat = message.forward_from_chat
    if chat.type != "channel":
        await message.answer(
            "❌ Это не канал. Перешлите сообщение именно из канала.",
            reply_markup=get_channel_setup_waiting_keyboard(),
        )
        return

    try:
        channel_obj = await channel_service.setup_channel(
            user_id=message.from_user.id,
            channel_id=chat.id,
            channel_username=chat.username,
            channel_title=chat.title,
            bot=message.bot,
        )
        if channel_obj:
            await state.clear()
            await message.answer(
                f"✅ <b>Канал подключён!</b>\n\n"
                f"📢 {chat.title}\n\n"
                "Все новые треки будут автоматически пересылаться в канал.",
                reply_markup=get_channel_back_keyboard(),
            )
        else:
            await message.answer(
                "❌ Не удалось подключить. Проверьте права бота.",
                reply_markup=get_channel_setup_waiting_keyboard(),
            )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка: {e}",
            reply_markup=get_channel_setup_waiting_keyboard(),
        )


# ---- Channel Help ----

@router.callback_query(F.data == "ch:help")
async def cb_channel_help(callback: CallbackQuery):
    await callback.message.edit_text(
        "❓ <b>Для чего нужен канал?</b>\n\n"
        "Канал — это ваше личное хранилище аудио в Telegram.\n\n"
        "• Все треки автоматически пересылаются в канал\n"
        "• Хэштеги для удобного поиска\n"
        "• Музыка доступна даже без бота\n"
        "• Telegram хранит файлы бессрочно\n\n"
        "<b>Как подключить:</b>\n"
        "1. Создайте приватный канал\n"
        "2. Добавьте бота администратором\n"
        "3. Перешлите любое сообщение из канала боту",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:channel")],
        ]),
    )
    await callback.answer()


# ---- Channel Scan (Проверить канал) ----

@router.callback_query(F.data == "ch:scan")
async def cb_channel_scan(callback: CallbackQuery):
    """Scan channel to rebuild message index"""
    user_id = callback.from_user.id

    if channel_service.is_sync_active(user_id):
        await callback.answer("Операция уже выполняется!", show_alert=True)
        return

    channel = await channel_service.get_user_channel(user_id)
    if not channel:
        await callback.answer("Канал не найден", show_alert=True)
        return

    title = channel.channel_title or "Канал"
    await callback.message.edit_text(
        f"🔍 <b>Проверка канала...</b>\n\n"
        f"📢 {title}\n"
        f"⏳ Сканирую сообщения...",
        reply_markup=get_channel_operation_keyboard("ch:op_cancel"),
    )
    await callback.answer()

    async def progress(scanned, audio_found, restored, current_id=0, max_id=0):
        pct = f" ({current_id * 100 // max_id}%)" if max_id else ""
        try:
            await callback.message.edit_text(
                f"🔍 <b>Проверка канала...{pct}</b>\n\n"
                f"📢 {title}\n"
                f"📨 Проверено: <b>{scanned}</b>\n"
                f"🎵 Аудио: <b>{audio_found}</b>\n"
                f"🔄 Восстановлено: <b>{restored}</b>",
                reply_markup=get_channel_operation_keyboard("ch:op_cancel"),
            )
        except Exception:
            pass

    result = await channel_service.scan_channel(
        user_id=user_id, bot=callback.bot, progress_callback=progress
    )

    if result.get("error"):
        await callback.message.edit_text(
            f"❌ Ошибка: {result['error']}",
            reply_markup=get_channel_back_keyboard(),
        )
        return

    cancelled = "\n⛔ <i>Прервано</i>" if result.get("cancelled") else ""
    await callback.message.edit_text(
        f"✅ <b>Проверка завершена!</b>{cancelled}\n\n"
        f"📨 Проверено: <b>{result['scanned']}</b>\n"
        f"🎵 Аудио: <b>{result['audio_found']}</b>\n"
        f"🔄 Восстановлено: <b>{result['restored']}</b>\n"
        f"✅ Уже в базе: <b>{result['already_known']}</b>",
        reply_markup=get_channel_back_keyboard(),
    )


# ---- Channel Restore Missing (Восстановить отсутствующие) ----

@router.callback_query(F.data == "ch:restore")
async def cb_channel_restore(callback: CallbackQuery):
    """Send tracks that are not yet in channel (pending)"""
    user_id = callback.from_user.id

    if channel_service.is_sync_active(user_id):
        await callback.answer("Операция уже выполняется!", show_alert=True)
        return

    channel = await channel_service.get_user_channel(user_id)
    if not channel:
        await callback.answer("Канал не найден", show_alert=True)
        return

    stats = await channel_service.get_sync_stats(user_id)
    if stats.get("error"):
        await callback.answer(stats["error"], show_alert=True)
        return

    if stats["to_sync"] == 0:
        await callback.message.edit_text(
            f"✅ <b>Все треки на месте!</b>\n\n"
            f"📢 {stats['channel_title']}\n"
            f"🎵 В канале: <b>{stats['already_synced']}</b>\n"
            f"📚 В библиотеке: <b>{stats['total_tracks']}</b>",
            reply_markup=get_channel_back_keyboard(),
        )
        await callback.answer()
        return

    title = stats["channel_title"]
    to_sync = stats["to_sync"]

    await callback.message.edit_text(
        f"📤 <b>Отправка треков...</b>\n\n"
        f"📢 {title}\n"
        f"📤 К отправке: <b>{to_sync}</b>\n\n"
        f"⏳ 0/{to_sync}",
        reply_markup=get_channel_operation_keyboard("ch:op_cancel"),
    )
    await callback.answer()

    async def progress(current, total, synced):
        try:
            await callback.message.edit_text(
                f"📤 <b>Отправка треков...</b>\n\n"
                f"📢 {title}\n"
                f"⏳ {synced}/{total}",
                reply_markup=get_channel_operation_keyboard("ch:op_cancel"),
            )
        except Exception:
            pass

    result = await channel_service.sync_all_tracks(
        user_id=user_id, bot=callback.bot, progress_callback=progress
    )

    if result.get("error"):
        await callback.message.edit_text(
            f"❌ Ошибка: {result['error']}",
            reply_markup=get_channel_back_keyboard(),
        )
        return

    if result.get("cancelled"):
        await callback.message.edit_text(
            f"⛔ <b>Прервано</b>\n\n"
            f"📤 Отправлено: <b>{result['synced']}</b>\n"
            f"⏭ Пропущено: <b>{result['skipped']}</b>",
            reply_markup=get_channel_back_keyboard(),
        )
        return

    await callback.message.edit_text(
        f"✅ <b>Готово!</b>\n\n"
        f"📤 Добавлено: <b>{result['synced']}</b>\n"
        f"⏭ Уже было: <b>{result['skipped']}</b>\n"
        f"❌ Ошибок: <b>{result['failed']}</b>",
        reply_markup=get_channel_back_keyboard(),
    )


# ---- Channel Duplicates ----

@router.callback_query(F.data == "ch:duplicates")
async def cb_channel_duplicates(callback: CallbackQuery, state: FSMContext):
    from bot.handlers.deduplication import start_dedup_flow

    await callback.answer()
    await start_dedup_flow(callback, state, callback.from_user.id)


# ---- Channel Reset (Очистить и пересканировать) ----

@router.callback_query(F.data == "ch:reset_confirm")
async def cb_channel_reset_confirm(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚠️ <b>Пересканировать канал?</b>\n\n"
        "Все записи ChannelMessage будут удалены,\n"
        "затем канал будет просканирован заново.\n\n"
        "Треки в канале <b>не удалятся</b>.",
        reply_markup=get_channel_reset_confirm_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "ch:reset")
async def cb_channel_reset(callback: CallbackQuery):
    """Clear ChannelMessage records and rescan"""
    user_id = callback.from_user.id
    channel = await channel_service.get_user_channel(user_id)
    if not channel:
        await callback.answer("Канал не найден", show_alert=True)
        return

    # Delete all ChannelMessage for this channel
    async with get_session() as session:
        await session.execute(
            ChannelMessage.__table__.delete().where(
                ChannelMessage.channel_id == channel.id
            )
        )

    title = channel.channel_title or "Канал"
    await callback.message.edit_text(
        f"🔄 <b>Записи очищены. Сканирую...</b>\n\n📢 {title}",
        reply_markup=get_channel_operation_keyboard("ch:op_cancel"),
    )
    await callback.answer()

    async def progress(scanned, audio_found, restored, current_id=0, max_id=0):
        pct = f" ({current_id * 100 // max_id}%)" if max_id else ""
        try:
            await callback.message.edit_text(
                f"🔍 <b>Пересканирование...{pct}</b>\n\n"
                f"📢 {title}\n"
                f"📨 Проверено: <b>{scanned}</b>\n"
                f"🎵 Аудио: <b>{audio_found}</b>\n"
                f"🔄 Найдено: <b>{restored}</b>",
                reply_markup=get_channel_operation_keyboard("ch:op_cancel"),
            )
        except Exception:
            pass

    result = await channel_service.scan_channel(
        user_id=user_id, bot=callback.bot, progress_callback=progress
    )

    if result.get("error"):
        await callback.message.edit_text(
            f"❌ Ошибка: {result['error']}",
            reply_markup=get_channel_back_keyboard(),
        )
        return

    await callback.message.edit_text(
        f"✅ <b>Пересканирование завершено!</b>\n\n"
        f"📨 Проверено: <b>{result['scanned']}</b>\n"
        f"🎵 Найдено: <b>{result['audio_found']}</b>",
        reply_markup=get_channel_back_keyboard(),
    )


# ---- Channel Settings ----

@router.callback_query(F.data == "ch:settings")
async def cb_channel_settings(callback: CallbackQuery):
    channel = await channel_service.get_user_channel(callback.from_user.id)
    if not channel:
        await callback.answer("Канал не найден", show_alert=True)
        return

    await callback.message.edit_text(
        f"⚙️ <b>Настройки канала</b>\n\n"
        f"📢 {channel.channel_title or 'Канал'}\n"
        f"#️⃣ Хэштеги: {'✅' if channel.include_hashtags else '❌'}",
        reply_markup=get_channel_settings_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "ch:disconnect_confirm")
async def cb_channel_disconnect_confirm(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚠️ <b>Отключить канал?</b>\n\n"
        "Треки останутся в канале,\n"
        "но новые не будут отправляться.",
        reply_markup=get_channel_disconnect_confirm_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "ch:disconnect")
async def cb_channel_disconnect(callback: CallbackQuery):
    await channel_service.disable_channel(callback.from_user.id)
    await callback.message.edit_text(
        "✅ Канал отключён.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main")],
        ]),
    )
    await callback.answer("Канал отключён")


@router.callback_query(F.data == "ch:op_cancel")
async def cb_channel_op_cancel(callback: CallbackQuery):
    """Cancel an ongoing channel operation (scan / restore)"""
    channel_service.request_cancel_sync(callback.from_user.id)
    await callback.answer("⛔ Прерывание...", show_alert=True)


# ═══════════════════════════════════════════════════════════
#                 STATISTICS  section
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "menu:stats")
async def cb_stats(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text = await _get_stats_text(callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=get_stats_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "stats:refresh")
async def cb_stats_refresh(callback: CallbackQuery):
    text = await _get_stats_text(callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=get_stats_menu_keyboard())
    await callback.answer("Обновлено!")


# ═══════════════════════════════════════════════════════════
#             TRACK-LEVEL  callbacks (kept here)
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("delete_track:"))
async def cb_delete_track(callback: CallbackQuery):
    track_id = int(callback.data.split(":")[1])
    track = await track_service.get_track(track_id)
    if not track:
        await callback.answer("Трек не найден", show_alert=True)
        return
    title = track.title or "Без названия"
    success = await track_service.delete_track(track_id)
    if success:
        await callback.message.edit_text(f"🗑 Трек <b>{title}</b> удалён.")
        await callback.answer("Удалено!")
    else:
        await callback.answer("Ошибка удаления", show_alert=True)


@router.callback_query(F.data.startswith("enrich_track:"))
async def cb_enrich_track(callback: CallbackQuery):
    track_id = int(callback.data.split(":")[1])
    await callback.answer("Обновление метаданных...")
    success = await track_service.trigger_enrichment(track_id)
    if success:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.reply("✅ Метаданные обновлены!")
    else:
        await callback.answer("Не удалось обновить", show_alert=True)


# ---- General ----

@router.callback_query(F.data == "cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Отменено.")
    await callback.answer()


@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery):
    await callback.answer()

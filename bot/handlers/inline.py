"""
TG Player Bot - Inline Mode Handler

Handles Telegram Inline Queries (@bot_username query):
- playlist:<id> or pl:<id> — Rich playlist card with "Open in Player" and "Get Files" buttons
- track:<id> or tr:<id> — Native Telegram Audio message with player button
- album:<id> or al:<id> — Album card with player and download buttons
- Text search (e.g. "@bot Queen") — Instant track/playlist search across library
- Empty query — Recent tracks and playlists
"""
import logging
import re
from typing import List, Union
from aiogram import Router, F, Bot
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultCachedAudio,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.enums import ParseMode
from sqlalchemy import select, or_, desc
from sqlalchemy.orm import selectinload

from shared.database import get_session
from shared.models import Track, Playlist, PlaylistTrack, Album, AlbumTrack, User
from shared.config import get_settings
from shared.utils import format_duration
from bot.services.delivery import deliver_playlist_tracks

logger = logging.getLogger(__name__)
router = Router()
settings = get_settings()


def _get_bot_username(bot: Bot) -> str:
    """Get active bot username or fallback"""
    return settings.bot_username or "tg_player_bot"


def _normalize_thumb_url(url: Union[str, None]) -> Union[str, None]:
    """Ensure thumbnail URL is a valid absolute http/https URL as required by Telegram Bot API"""
    if not url or not isinstance(url, str):
        return None
    cleaned = url.strip()
    if cleaned.startswith("http://") or cleaned.startswith("https://"):
        return cleaned
    if cleaned.startswith("/"):
        base = (settings.api_url or "").rstrip("/")
        if base.startswith("http://") or base.startswith("https://"):
            return f"{base}{cleaned}"
    return None


def _format_playlist_card(playlist: Playlist, tracks: list, bot_username: str) -> tuple[str, InlineKeyboardMarkup]:
    """Format HTML card and keyboard for a playlist"""
    total_sec = sum(t.duration or 0 for t in tracks)
    dur_str = format_duration(total_sec) if total_sec else "0:00"
    owner_name = playlist.owner.display_name if playlist.owner else settings.display_name

    text = (
        f"🎧 <b>{playlist.name}</b>\n"
    )
    if playlist.description:
        text += f"<i>{playlist.description.strip()}</i>\n\n"
    else:
        text += "\n"

    text += (
        f"📊 <b>Треков:</b> {len(tracks)}  |  ⏱ <b>Длительность:</b> {dur_str}\n"
        f"👤 <b>Автор:</b> {owner_name}\n\n"
        f"🎵 <i>{settings.display_name} — Музыкальная медиатека</i>"
    )

    track_count_text = f" ({len(tracks)})" if tracks else ""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎵 Открыть в плеере",
                url=f"https://t.me/{bot_username}?startapp=playlist_{playlist.id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"📥 Получить файлы{track_count_text}",
                url=f"https://t.me/{bot_username}?start=files_playlist_{playlist.id}"
            )
        ]
    ])
    return text, keyboard


def _format_album_card(album: Album, tracks: list, bot_username: str) -> tuple[str, InlineKeyboardMarkup]:
    """Format HTML card and keyboard for an album"""
    total_sec = sum(t.duration or 0 for t in tracks)
    dur_str = format_duration(total_sec) if total_sec else "0:00"

    text = (
        f"💿 <b>Альбом: {album.name}</b>\n"
        f"👤 <b>Исполнитель:</b> {album.artist or 'Неизвестен'}\n"
        f"📊 <b>Треков:</b> {len(tracks)}  |  ⏱ <b>Длительность:</b> {dur_str}\n\n"
        f"🎵 <i>{settings.display_name}</i>"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎵 Слушать альбом в плеере",
                url=f"https://t.me/{bot_username}?startapp=album_{album.id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"📥 Получить файлы ({len(tracks)})",
                url=f"https://t.me/{bot_username}?start=files_album_{album.id}"
            )
        ]
    ])
    return text, keyboard


@router.inline_query()
async def handle_inline_query(query: InlineQuery, bot: Bot):
    """Handle all inline requests from Telegram users"""
    raw_query = query.query.strip()
    user_id = query.from_user.id
    bot_username = _get_bot_username(bot)
    results = []

    try:
        async with get_session() as session:
            # 1. Check for specific commands: playlist:<id> or pl:<id>
            pl_match = re.match(r'^(?:playlist|pl)[:_](\d+)$', raw_query, re.IGNORECASE)
            if pl_match:
                pl_id = int(pl_match.group(1))
                pl_result = await session.execute(
                    select(Playlist)
                    .options(
                        selectinload(Playlist.tracks).selectinload(PlaylistTrack.track).selectinload(Track.enrichment),
                        selectinload(Playlist.owner)
                    )
                    .where(Playlist.id == pl_id)
                )
                playlist = pl_result.scalar()
                if playlist:
                    tracks = [pt.track for pt in playlist.tracks if pt.track]
                    card_text, card_markup = _format_playlist_card(playlist, tracks, bot_username)
                    raw_thumb = playlist.custom_cover_url or (tracks[0].cover_url if tracks and tracks[0].cover_url else None)

                    results.append(
                        InlineQueryResultArticle(
                            id=f"pl_{playlist.id}",
                            title=f"📁 Плейлист: {playlist.name}",
                            description=f"{len(tracks)} треков • Открыть в плеере / Скачать",
                            thumbnail_url=_normalize_thumb_url(raw_thumb),
                            input_message_content=InputTextMessageContent(
                                message_text=card_text,
                                parse_mode=ParseMode.HTML
                            ),
                            reply_markup=card_markup
                        )
                    )

                await query.answer(results=results, cache_time=10, is_personal=True)
                return

            # 2. Check for specific track command: track:<id> or tr:<id>
            tr_match = re.match(r'^(?:track|tr)[:_](\d+)$', raw_query, re.IGNORECASE)
            if tr_match:
                tr_id = int(tr_match.group(1))
                track = await session.scalar(
                    select(Track)
                    .options(selectinload(Track.enrichment))
                    .where(Track.id == tr_id)
                )
                if track and track.file_id:
                    caption = f"🎧 <b>{track.artist or 'Неизвестен'} — {track.title or 'Без названия'}</b>"
                    if track.album:
                        caption += f"\n💿 <i>{track.album}</i>"
                    caption += f"\n\n🎵 <i>{settings.display_name}</i>"

                    markup = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🎵 Слушать в плеере",
                                url=f"https://t.me/{bot_username}?startapp=track_{track.id}"
                            )
                        ]
                    ])

                    results.append(
                        InlineQueryResultCachedAudio(
                            id=f"track_{track.id}",
                            audio_file_id=track.file_id,
                            caption=caption,
                            parse_mode=ParseMode.HTML,
                            reply_markup=markup
                        )
                    )

                await query.answer(results=results, cache_time=10, is_personal=True)
                return

            # 3. Check for specific album command: album:<id> or al:<id>
            al_match = re.match(r'^(?:album|al)[:_](\d+)$', raw_query, re.IGNORECASE)
            if al_match:
                al_id = int(al_match.group(1))
                al_res = await session.execute(
                    select(Album)
                    .options(selectinload(Album.tracks).selectinload(AlbumTrack.track).selectinload(Track.enrichment))
                    .where(Album.id == al_id)
                )
                album = al_res.scalar()
                if album:
                    tracks = [at.track for at in album.tracks if at.track]
                    card_text, card_markup = _format_album_card(album, tracks, bot_username)
                    results.append(
                        InlineQueryResultArticle(
                            id=f"album_{album.id}",
                            title=f"💿 Альбом: {album.name}",
                            description=f"{album.artist or 'Артист'} • {len(tracks)} треков",
                            thumbnail_url=_normalize_thumb_url(album.cover_url),
                            input_message_content=InputTextMessageContent(
                                message_text=card_text,
                                parse_mode=ParseMode.HTML
                            ),
                            reply_markup=card_markup
                        )
                    )

                await query.answer(results=results, cache_time=10, is_personal=True)
                return

            # 4. Search query or Empty query
            if raw_query:
                search_term = f"%{raw_query}%"

                # Search tracks
                tracks_query = (
                    select(Track)
                    .options(selectinload(Track.enrichment))
                    .where(
                        Track.file_id.is_not(None),
                        or_(
                            Track.title.ilike(search_term),
                            Track.artist.ilike(search_term),
                            Track.file_name.ilike(search_term)
                        )
                    )
                    .order_by(desc(Track.play_count), desc(Track.id))
                    .limit(20)
                )
                tracks_result = await session.execute(tracks_query)
                found_tracks = tracks_result.scalars().all()

                for t in found_tracks:
                    caption = f"🎧 <b>{t.artist or 'Неизвестен'} — {t.title or 'Без названия'}</b>"
                    if t.album:
                        caption += f"\n💿 <i>{t.album}</i>"
                    caption += f"\n\n🎵 <i>{settings.display_name}</i>"

                    markup = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🎵 Слушать в плеере",
                                url=f"https://t.me/{bot_username}?startapp=track_{t.id}"
                            )
                        ]
                    ])

                    results.append(
                        InlineQueryResultCachedAudio(
                            id=f"tr_s_{t.id}",
                            audio_file_id=t.file_id,
                            caption=caption,
                            parse_mode=ParseMode.HTML,
                            reply_markup=markup
                        )
                    )

                # Search playlists
                playlists_query = (
                    select(Playlist)
                    .options(
                        selectinload(Playlist.tracks).selectinload(PlaylistTrack.track).selectinload(Track.enrichment),
                        selectinload(Playlist.owner)
                    )
                    .where(
                        Playlist.name.ilike(search_term),
                        or_(Playlist.is_public == True, Playlist.owner_id == user_id)
                    )
                    .limit(5)
                )
                pl_res = await session.execute(playlists_query)
                found_playlists = pl_res.scalars().all()

                for pl in found_playlists:
                    tracks = [pt.track for pt in pl.tracks if pt.track]
                    card_text, card_markup = _format_playlist_card(pl, tracks, bot_username)
                    raw_thumb = pl.custom_cover_url or (tracks[0].cover_url if tracks and tracks[0].cover_url else None)

                    results.append(
                        InlineQueryResultArticle(
                            id=f"pl_s_{pl.id}",
                            title=f"📁 Плейлист: {pl.name}",
                            description=f"{len(tracks)} треков",
                            thumbnail_url=_normalize_thumb_url(raw_thumb),
                            input_message_content=InputTextMessageContent(
                                message_text=card_text,
                                parse_mode=ParseMode.HTML
                            ),
                            reply_markup=card_markup
                        )
                    )

            else:
                # Empty query — show popular/recent tracks and user playlists
                # 1. User playlists or public playlists
                pl_query = (
                    select(Playlist)
                    .options(
                        selectinload(Playlist.tracks).selectinload(PlaylistTrack.track).selectinload(Track.enrichment),
                        selectinload(Playlist.owner)
                    )
                    .where(or_(Playlist.owner_id == user_id, Playlist.is_public == True))
                    .order_by(desc(Playlist.updated_at))
                    .limit(5)
                )
                pl_res = await session.execute(pl_query)
                for pl in pl_res.scalars().all():
                    tracks = [pt.track for pt in pl.tracks if pt.track]
                    card_text, card_markup = _format_playlist_card(pl, tracks, bot_username)
                    raw_thumb = pl.custom_cover_url or (tracks[0].cover_url if tracks and tracks[0].cover_url else None)

                    results.append(
                        InlineQueryResultArticle(
                            id=f"pl_top_{pl.id}",
                            title=f"📁 Плейлист: {pl.name}",
                            description=f"{len(tracks)} треков • Нажмите для отправки",
                            thumbnail_url=_normalize_thumb_url(raw_thumb),
                            input_message_content=InputTextMessageContent(
                                message_text=card_text,
                                parse_mode=ParseMode.HTML
                            ),
                            reply_markup=card_markup
                        )
                    )

                # 2. Recent tracks
                tracks_query = (
                    select(Track)
                    .options(selectinload(Track.enrichment))
                    .where(Track.file_id.is_not(None))
                    .order_by(desc(Track.id))
                    .limit(15)
                )
                tr_res = await session.execute(tracks_query)
                for t in tr_res.scalars().all():
                    caption = f"🎧 <b>{t.artist or 'Неизвестен'} — {t.title or 'Без названия'}</b>"
                    if t.album:
                        caption += f"\n💿 <i>{t.album}</i>"
                    caption += f"\n\n🎵 <i>{settings.display_name}</i>"

                    markup = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🎵 Слушать в плеере",
                                url=f"https://t.me/{bot_username}?startapp=track_{t.id}"
                            )
                        ]
                    ])

                    results.append(
                        InlineQueryResultCachedAudio(
                            id=f"tr_top_{t.id}",
                            audio_file_id=t.file_id,
                            caption=caption,
                            parse_mode=ParseMode.HTML,
                            reply_markup=markup
                        )
                    )

        await query.answer(
            results=results,
            cache_time=5,
            is_personal=True,
            switch_pm_text="🎵 Открыть плеер TG Player",
            switch_pm_parameter="open_player"
        )
    except Exception as e:
        logger.error(f"Error handling inline query: {e}", exc_info=True)
        await query.answer(results=[], cache_time=5)


@router.callback_query(F.data.startswith("inline_dl_pl:"))
async def handle_inline_playlist_download(callback: CallbackQuery, bot: Bot):
    """
    Handle callback from an inline playlist card.
    Because inline messages have no chat.id, we send files to callback.from_user.id in DM.
    """
    playlist_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    bot_username = _get_bot_username(bot)

    try:
        # Deliver to user's direct messages
        await deliver_playlist_tracks(bot, chat_id=user_id, playlist_id=playlist_id, user_id=user_id)
        await callback.answer("✅ Отправляю файлы плейлиста вам в личные сообщения с ботом!", show_alert=False)
    except Exception as e:
        logger.warning(f"Could not send inline playlist files to user {user_id}: {e}")
        await callback.answer(
            f"⚠️ Чтобы бот мог отправить вам файлы, откройте диалог с @{bot_username} и нажмите «Начать» (/start)!",
            show_alert=True
        )

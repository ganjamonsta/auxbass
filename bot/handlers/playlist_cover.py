"""
TG Player Bot - Playlist Cover Handler

Handles playlist cover uploads from the Mini App.
Workflow:
1. User clicks on playlist cover in webapp editor
2. Webapp calls API which sends message with ForceReply
3. User replies to message with a photo
4. Bot crops photo to square, uploads to user's channel for backup
5. Cover URL (via API proxy) is saved to playlist
"""
from typing import Optional
from io import BytesIO
import logging
import re

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, BufferedInputFile, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from PIL import Image, ImageOps
from sqlalchemy import select

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import get_session
from shared.models import Playlist, UserChannel
from shared.config import get_settings
from bot.handlers.keyboards import get_cancel_keyboard

router = Router()
settings = get_settings()
logger = logging.getLogger(__name__)

# Target size for cover images (square)
COVER_SIZE = 500

# Regex to parse cover data from reply_to_message
COVER_DATA_PATTERN = re.compile(r'cover:(\d+):(-?\d+)')


class PlaylistCoverStates(StatesGroup):
    waiting_for_cover = State()


@router.message(CommandStart(deep_link=True))
async def cmd_start_cover(message: Message, command: CommandObject, state: FSMContext):
    """Handle /start cover_<playlist_id>"""
    args = command.args
    if not args or not args.startswith("cover_"):
        return  # Not a cover deep link, let other handlers process
    
    try:
        playlist_id = int(args.replace("cover_", ""))
    except ValueError:
        await message.answer("❌ Неверная ссылка")
        return

    user_id = message.from_user.id

    async with get_session() as session:
        # Check playlist exists and user owns it
        playlist = await session.get(Playlist, playlist_id)
        if not playlist:
            await message.answer("❌ Плейлист не найден")
            return
        
        if playlist.owner_id != user_id:
            await message.answer("❌ Вы не являетесь владельцем этого плейлиста")
            return
        
        # Check if user has connected channel (required for cover storage)
        channel = await session.scalar(
            select(UserChannel).where(
                UserChannel.user_id == user_id,
                UserChannel.is_active == True
            )
        )
        
        if not channel:
            await message.answer(
                "🔒 <b>Подключите канал для загрузки обложек</b>\n\n"
                "Обложки плейлистов хранятся в вашем Telegram-канале.\n\n"
                "Используйте команду /channel для подключения.",
                parse_mode="HTML"
            )
            return
        
        # Save state for cover upload
        await state.set_state(PlaylistCoverStates.waiting_for_cover)
        await state.update_data(
            playlist_id=playlist_id,
            playlist_name=playlist.name,
            channel_id=channel.channel_id
        )
        
        await message.answer(
            f"📷 <b>Загрузка обложки для плейлиста</b>\n\n"
            f"🎵 <i>{playlist.name}</i>\n\n"
            "Отправьте изображение. Я автоматически обрежу его до квадрата по центру.",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )


@router.message(PlaylistCoverStates.waiting_for_cover, F.photo)
async def handle_cover_upload(message: Message, state: FSMContext, bot: Bot):
    """Process uploaded cover photo"""
    data = await state.get_data()
    playlist_id = data.get("playlist_id")
    playlist_name = data.get("playlist_name", "Плейлист")
    channel_id = data.get("channel_id")
    
    if not playlist_id or not channel_id:
        await state.clear()
        await message.answer("❌ Ошибка: данные сессии потеряны. Попробуйте заново.")
        return
    
    status_msg = await message.answer("⏳ Обрабатываю изображение...")
    
    try:
        # Get highest resolution photo
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        
        # Download the file
        downloaded_file = await bot.download_file(file_info.file_path)
        
        # Open with Pillow
        img = Image.open(downloaded_file)
        
        # Convert to RGB if necessary (for JPEG saving)
        if img.mode in ('RGBA', 'P', 'LA'):
            # Create white background for transparent images
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Center crop to square with the target size
        img = ImageOps.fit(
            img, 
            (COVER_SIZE, COVER_SIZE), 
            method=Image.Resampling.LANCZOS, 
            centering=(0.5, 0.5)
        )
        
        # Save to buffer
        output = BytesIO()
        img.save(output, format="JPEG", quality=90)
        output.seek(0)
        
        # Upload to user's channel for persistent storage
        await status_msg.edit_text("⏳ Сохраняю в ваш канал...")
        
        try:
            # Send to user's backup channel
            sent_msg = await bot.send_photo(
                chat_id=channel_id,
                photo=BufferedInputFile(output.read(), filename=f"cover_{playlist_id}.jpg"),
                caption=f"🎵 Обложка плейлиста: <b>{playlist_name}</b>",
                parse_mode="HTML"
            )
            
            # Get file_id from sent message
            cover_file_id = sent_msg.photo[-1].file_id
            
        except TelegramForbiddenError:
            # Bot was removed from channel
            await status_msg.edit_text(
                "❌ Бот был удалён из вашего канала.\n\n"
                "Переподключите канал командой /channel"
            )
            await state.clear()
            return
            
        except TelegramBadRequest as e:
            logger.error(f"Failed to upload cover to channel {channel_id}: {e}")
            await status_msg.edit_text(
                "❌ Не удалось загрузить обложку в канал.\n\n"
                "Проверьте, что бот добавлен в канал как администратор."
            )
            await state.clear()
            return
        
        # Generate cover URL through API proxy
        # api_url may already contain /api, so use /images/ path only
        base_url = settings.api_url.rstrip('/').removesuffix('/api')
        cover_url = f"{base_url}/api/images/{cover_file_id}"
        
        # Update playlist in database
        async with get_session() as session:
            playlist = await session.get(Playlist, playlist_id)
            if playlist:
                playlist.cover_url = cover_url
                await session.commit()
                logger.info(f"Cover updated for playlist {playlist_id}: {cover_url}")
        
        # Send success message with preview
        await status_msg.delete()
        
        # Re-read the buffer for preview
        output.seek(0)
        await message.answer_photo(
            BufferedInputFile(output.read(), filename="cover_preview.jpg"),
            caption=(
                f"✅ <b>Обложка обновлена!</b>\n\n"
                f"🎵 Плейлист: <i>{playlist_name}</i>\n\n"
                f"Обложка сохранена в ваш канал и будет отображаться в плеере."
            ),
            parse_mode="HTML"
        )
        
        await state.clear()
        
    except Exception as e:
        logger.exception(f"Error processing cover upload: {e}")
        await status_msg.edit_text(f"❌ Ошибка при обработке: {str(e)}")
        await state.clear()


@router.message(PlaylistCoverStates.waiting_for_cover, F.document)
async def handle_cover_document(message: Message, state: FSMContext):
    """Handle document uploads - inform user to send as photo"""
    doc = message.document
    if doc.mime_type and doc.mime_type.startswith("image/"):
        await message.reply(
            "💡 Отправьте изображение как <b>фото</b>, а не как документ.\n\n"
            "При отправке уберите галочку «Сжать изображение» или "
            "просто отправьте фото обычным способом.",
            parse_mode="HTML"
        )
    else:
        await message.reply(
            "❌ Пожалуйста, отправьте изображение.",
            reply_markup=get_cancel_keyboard()
        )


@router.message(PlaylistCoverStates.waiting_for_cover)
async def handle_cover_invalid(message: Message, state: FSMContext):
    """Handle invalid messages while waiting for cover"""
    await message.reply(
        "❌ Пожалуйста, отправьте изображение для обложки.",
        reply_markup=get_cancel_keyboard()
    )


@router.callback_query(F.data == "cancel", PlaylistCoverStates.waiting_for_cover)
async def cancel_cover_upload(callback: CallbackQuery, state: FSMContext):
    """Cancel cover upload (FSM state)"""
    await state.clear()
    await callback.message.edit_text("❌ Загрузка обложки отменена")
    await callback.answer()


@router.message(F.photo, F.reply_to_message)
async def handle_photo_reply_for_cover(message: Message, state: FSMContext, bot: Bot):
    """
    Handle photo sent as reply to cover upload request.
    Parses playlist_id and channel_id from replied message text.
    No database storage needed!
    """
    # First check if FSM state is active (handled by handle_cover_upload)
    current_state = await state.get_state()
    if current_state == PlaylistCoverStates.waiting_for_cover:
        return  # Will be handled by handle_cover_upload
    
    # Check if replied message contains cover data
    reply_msg = message.reply_to_message
    if not reply_msg or not reply_msg.text:
        return  # Not a cover request reply
    
    # Parse cover data from message: cover:playlist_id:channel_id
    match = COVER_DATA_PATTERN.search(reply_msg.text)
    if not match:
        return  # Not a cover request
    
    playlist_id = int(match.group(1))
    channel_id = int(match.group(2))
    
    user_id = message.from_user.id
    
    # Get playlist info
    async with get_session() as session:
        playlist = await session.get(Playlist, playlist_id)
        if not playlist:
            await message.answer("❌ Плейлист не найден")
            return
        
        if playlist.owner_id != user_id:
            await message.answer("❌ Вы не являетесь владельцем этого плейлиста")
            return
        
        playlist_name = playlist.name
    
    # Process the cover
    status_msg = await message.answer("⏳ Обрабатываю изображение...")
    
    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        
        img = Image.open(downloaded_file)
        
        if img.mode in ('RGBA', 'P', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        img = ImageOps.fit(
            img, 
            (COVER_SIZE, COVER_SIZE), 
            method=Image.Resampling.LANCZOS, 
            centering=(0.5, 0.5)
        )
        
        output = BytesIO()
        img.save(output, format="JPEG", quality=90)
        output.seek(0)
        
        await status_msg.edit_text("⏳ Сохраняю в ваш канал...")
        
        try:
            sent_msg = await bot.send_photo(
                chat_id=channel_id,
                photo=BufferedInputFile(output.read(), filename=f"cover_{playlist_id}.jpg"),
                caption=f"🎵 Обложка плейлиста: <b>{playlist_name}</b>",
                parse_mode="HTML"
            )
            cover_file_id = sent_msg.photo[-1].file_id
            
        except TelegramForbiddenError:
            await status_msg.edit_text(
                "❌ Бот был удалён из вашего канала.\n\n"
                "Переподключите канал командой /channel"
            )
            return
            
        except TelegramBadRequest as e:
            logger.error(f"Failed to upload cover to channel {channel_id}: {e}")
            await status_msg.edit_text(
                "❌ Не удалось загрузить обложку в канал.\n\n"
                "Проверьте, что бот добавлен в канал как администратор."
            )
            return
        
        base_url = settings.api_url.rstrip('/').removesuffix('/api')
        cover_url = f"{base_url}/api/images/{cover_file_id}"
        
        async with get_session() as session:
            playlist = await session.get(Playlist, playlist_id)
            if playlist:
                playlist.cover_url = cover_url
                await session.commit()
                logger.info(f"Cover updated for playlist {playlist_id}: {cover_url}")
        
        await status_msg.delete()
        
        # Delete the request message to clean up
        try:
            await reply_msg.delete()
        except Exception:
            pass  # Ignore if can't delete
        
        output.seek(0)
        await message.answer_photo(
            BufferedInputFile(output.read(), filename="cover_preview.jpg"),
            caption=(
                f"✅ <b>Обложка обновлена!</b>\n\n"
                f"🎵 Плейлист: <i>{playlist_name}</i>\n\n"
                f"Обложка сохранена в ваш канал и будет отображаться в плеере."
            ),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.exception(f"Error processing cover upload: {e}")
        await status_msg.edit_text(f"❌ Ошибка при обработке: {str(e)}")

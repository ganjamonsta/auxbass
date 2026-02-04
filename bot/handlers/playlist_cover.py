"""
TG Player Bot - Playlist Cover Handler

Simplified workflow:
1. User clicks on playlist cover in webapp editor
2. Webapp calls API which sends message with ForceReply
3. User replies to message with a photo
4. Bot crops photo to square, uploads to user's channel, saves cover_url directly
"""
from io import BytesIO
import logging
import re

from aiogram import Router, F, Bot
from aiogram.types import Message, BufferedInputFile
from PIL import Image, ImageOps

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import get_session
from shared.models import Playlist
from shared.config import get_settings

router = Router()
settings = get_settings()
logger = logging.getLogger(__name__)

# Target size for cover images (square)
COVER_SIZE = 500

# Regex to parse cover data from reply_to_message: cover:playlist_id:channel_id
COVER_DATA_PATTERN = re.compile(r'cover:(\d+):(-?\d+)')


async def process_cover_image(bot: Bot, photo_file_id: str) -> bytes:
    """Download and process cover image to square JPEG."""
    file_info = await bot.get_file(photo_file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    
    img = Image.open(downloaded_file)
    
    # Convert to RGB
    if img.mode in ('RGBA', 'P', 'LA'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Center crop to square
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
    return output.read()


@router.message(F.photo, F.reply_to_message)
async def handle_cover_reply(message: Message, bot: Bot):
    """
    Handle photo sent as reply to cover upload request.
    Saves cover directly to channel and updates playlist.
    """
    reply_msg = message.reply_to_message
    if not reply_msg or not reply_msg.text:
        return
    
    # Parse cover data: cover:playlist_id:channel_id
    match = COVER_DATA_PATTERN.search(reply_msg.text)
    if not match:
        return
    
    playlist_id = int(match.group(1))
    channel_id = int(match.group(2))
    user_id = message.from_user.id
    
    logger.info(f"Processing cover for playlist {playlist_id} from user {user_id}")
    
    # Verify ownership
    async with get_session() as session:
        playlist = await session.get(Playlist, playlist_id)
        if not playlist or playlist.owner_id != user_id:
            await message.answer("❌ Плейлист не найден или нет доступа")
            return
        playlist_name = playlist.name
        old_cover_message_id = playlist.cover_message_id
    
    status_msg = await message.answer("⏳ Обрабатываю изображение...")
    
    try:
        # Process image
        photo = message.photo[-1]
        processed_image = await process_cover_image(bot, photo.file_id)
        
        await status_msg.edit_text("⏳ Сохраняю обложку...")
        
        # Delete old cover from channel if exists
        if old_cover_message_id:
            try:
                await bot.delete_message(channel_id, old_cover_message_id)
            except Exception:
                pass
        
        # Send new cover to channel
        cover_msg = await bot.send_photo(
            channel_id,
            BufferedInputFile(processed_image, filename=f"cover_{playlist_id}.jpg"),
            caption=f"🎵 Обложка: {playlist_name}"
        )
        
        # Get file_id and build URL
        new_file_id = cover_msg.photo[-1].file_id
        base_url = settings.webapp_url.rstrip('/')
        cover_url = f"{base_url}/api/images/{new_file_id}"
        
        # Update playlist
        async with get_session() as session:
            playlist = await session.get(Playlist, playlist_id)
            if playlist:
                playlist.cover_url = cover_url
                playlist.cover_message_id = cover_msg.message_id
                playlist.pending_cover_file_id = None  # Clear any pending
        
        await status_msg.delete()
        
        # Notify user
        await message.answer(
            f"✅ <b>Обложка установлена!</b>\n\n"
            f"🎵 Плейлист: <i>{playlist_name}</i>",
            parse_mode="HTML"
        )
        
        # Clean up request message
        try:
            await reply_msg.delete()
        except Exception:
            pass
            
    except Exception as e:
        logger.exception(f"Error processing cover: {e}")
        await status_msg.edit_text(f"❌ Ошибка: {str(e)}")


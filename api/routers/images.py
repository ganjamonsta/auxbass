import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from shared.config import get_settings
from api.routers.player import get_http_session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Images"])
settings = get_settings()

# Shared bot instance for image proxy (avoids creating a new Bot per request)
_image_bot: Optional[Bot] = None


def _get_bot() -> Bot:
    """Get or create shared bot instance for image proxy."""
    global _image_bot
    if _image_bot is None:
        _image_bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
    return _image_bot


async def close_image_bot():
    """Close shared bot session on shutdown."""
    global _image_bot
    if _image_bot is not None:
        try:
            await _image_bot.session.close()
        except Exception as e:
            logger.warning(f"Error closing image bot session: {e}")
        _image_bot = None


@router.get("/images/{file_id}")
async def get_image(file_id: str):
    """Proxy image from Telegram"""
    # Validate file_id format (Telegram file_ids are base64-like strings, 30-200 chars)
    if not file_id or len(file_id) < 20 or len(file_id) > 200:
        raise HTTPException(status_code=400, detail="Invalid file ID")
    # Reject obviously invalid characters (Telegram file_ids are alphanumeric + - _ )
    import re
    if not re.match(r'^[A-Za-z0-9_\-]+$', file_id):
        raise HTTPException(status_code=400, detail="Invalid file ID format")
    
    bot = _get_bot()
    
    try:
        # Get file path
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        
        # Construct download URL
        base_url = settings.telegram_api_url.rstrip("/")
        url = f"{base_url}/file/bot{settings.bot_token}/{file_path}"
            
        # Download and serve using shared pooled session
        session = await get_http_session()
        async with session.get(url) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=404, detail="Image not found")
            
            content = await resp.read()
            
            # Determine content type
            content_type = "image/jpeg"
            if file_path.endswith(".png"):
                content_type = "image/png"
            elif file_path.endswith(".webp"):
                content_type = "image/webp"
            
            return Response(
                content=content, 
                media_type=content_type,
                headers={"Cache-Control": "public, max-age=86400"}  # Cache for 24h
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to proxy image {file_id[:30]}...: {e}")
        raise HTTPException(status_code=404, detail="Image not found")

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import aiohttp
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from shared.config import get_settings

router = APIRouter(tags=["Images"])
settings = get_settings()

# Shared bot instance for image proxy (avoids creating a new Bot per request)
_image_bot: Bot = None


def _get_bot() -> Bot:
    """Get or create shared bot instance for image proxy."""
    global _image_bot
    if _image_bot is None or _image_bot.session.closed:
        _image_bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
    return _image_bot


@router.get("/images/{file_id}")
async def get_image(file_id: str):
    """Proxy image from Telegram"""
    bot = _get_bot()
    
    try:
        # Get file path
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        
        # Construct download URL
        base_url = settings.telegram_api_url.rstrip("/")
        url = f"{base_url}/file/bot{settings.bot_token}/{file_path}"
            
        # Download and serve
        async with aiohttp.ClientSession() as session:
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
        raise HTTPException(status_code=404, detail=str(e))

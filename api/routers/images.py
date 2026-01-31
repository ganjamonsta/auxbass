from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import aiohttp
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from shared.config import get_settings

router = APIRouter(tags=["Images"])
settings = get_settings()

@router.get("/images/{file_id}")
async def get_image(file_id: str):
    """Proxy image from Telegram"""
    # Create bot instance just to get file path
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    try:
        # Get file path
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        
        # Construct download URL
        # Handle custom API URL (e.g. local server)
        base_url = settings.telegram_api_url.rstrip("/")
        if "api.telegram.org" in base_url:
            url = f"{base_url}/file/bot{settings.bot_token}/{file_path}"
        else:
            # Local server usually follows same structure
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
                
                return Response(content=content, media_type=content_type)
                
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    finally:
        await bot.session.close()

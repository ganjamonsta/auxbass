"""
TG Player Bot v2 - Entry Point

Uses new modular service architecture.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from shared.config import get_settings
from shared.database import init_db, close_db

from bot.handlers.audio import router as audio_router
from bot.handlers.commands import router as commands_router
from bot.handlers.callbacks import router as callbacks_router
from bot.handlers.download import router as download_router
from bot.handlers.playlist_cover import router as playlist_cover_router
from bot.handlers.deduplication import router as deduplication_router

from bot.services.enrichment import enrichment_worker
from bot.services.channels import init_channel_service, start_channel_service, stop_channel_service


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point"""
    settings = get_settings()
    
    # Initialize database
    logger.info("Initializing database...")
    await init_db()
    
    # Start enrichment worker
    logger.info("Starting enrichment worker...")
    await enrichment_worker.start(
        idle_interval=60,   # Check every 60s when no pending tracks
        busy_interval=5     # Check every 5s when processing
    )
    
    # Initialize bot
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Initialize channel service with bot
    init_channel_service(bot)
    
    # Start channel forward queue worker
    logger.info("Starting channel forward queue worker...")
    await start_channel_service()
    
    # Initialize dispatcher with FSM storage
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register routers
    dp.include_router(playlist_cover_router)  # Must be before commands_router to handle deep links
    dp.include_router(deduplication_router)
    dp.include_router(commands_router)
    dp.include_router(audio_router)
    dp.include_router(callbacks_router)
    dp.include_router(download_router)
    
    # Start polling
    logger.info("Starting bot v2...")
    try:
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down...")
        await stop_channel_service()
        await enrichment_worker.stop()
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

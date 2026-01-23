"""
TG Player Bot - Entry Point
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

from handlers import commands, audio, callbacks, download
from services.enrichment import enrichment_worker


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
    await enrichment_worker.start(interval=30)  # Check every 30s when idle, 5s when busy
    
    # Initialize bot
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Initialize dispatcher with FSM storage
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register routers
    dp.include_router(commands.router)
    dp.include_router(audio.router)
    dp.include_router(callbacks.router)
    dp.include_router(download.router)
    
    # Start polling
    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    finally:
        await enrichment_worker.stop()
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

"""
TG Player - Unified Application Runner
Запускает одновременно FastAPI (API + WebApp статика) и Telegram Bot (aiogram)
в одном процессе. Идеально для Pterodactyl, Docker и одиночных контейнеров.
"""
import asyncio
import logging
import os
import signal
import sys

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from shared.config import get_settings
from shared.database import init_db, close_db
from bot.handlers.menu import router as menu_router
from bot.handlers.audio import router as audio_router
from bot.handlers.download import router as download_router
from bot.handlers.deduplication import router as deduplication_router
from bot.handlers.channel_pins import router as channel_pins_router

from bot.services.enrichment import enrichment_worker
from bot.services.channels import init_channel_service, start_channel_service, stop_channel_service
from api.main import app as fastapi_app

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("tg_player.runner")


async def run_server(host: str, port: int):
    """Запуск Uvicorn сервера с FastAPI"""
    config = uvicorn.Config(
        app=fastapi_app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
    )
    server = uvicorn.Server(config)
    logger.info(f"🌐 WebApp & API запускаются на http://{host}:{port}")
    await server.serve()


async def run_bot():
    """Запуск Telegram бота"""
    settings = get_settings()
    
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    init_channel_service(bot)
    
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    dp.include_router(deduplication_router)
    dp.include_router(menu_router)
    dp.include_router(audio_router)
    dp.include_router(download_router)
    dp.include_router(channel_pins_router)
    
    logger.info("🤖 Telegram Bot запускается (long polling)...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


async def main():
    settings = get_settings()
    
    # Порт для Pterodactyl (переменные SERVER_PORT или PORT)
    port = int(os.environ.get("SERVER_PORT") or os.environ.get("PORT") or settings.api_port)
    host = os.environ.get("SERVER_HOST") or settings.api_host
    
    logger.info("==========================================")
    logger.info("       TG Player - Universal Runner       ")
    logger.info("==========================================")
    logger.info(f"Домен: {settings.webapp_url}")
    logger.info(f"База данных: {settings.database_url}")
    logger.info(f"Порт: {port}")
    
    # Инициализация БД и фоновых воркеров
    await init_db()
    
    logger.info("Запуск enrichment worker...")
    await enrichment_worker.start(idle_interval=60, busy_interval=5)
    
    # Запускаем задачи одновременно
    server_task = asyncio.create_task(run_server(host, port))
    bot_task = asyncio.create_task(run_bot())
    
    tasks = [server_task, bot_task]
    
    try:
        # Ожидаем завершения или ошибки в любой из задач
        done, pending = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_EXCEPTION
        )
        for task in done:
            if task.exception():
                logger.error(f"Задача упала с ошибкой: {task.exception()}")
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Получен сигнал завершения...")
    finally:
        logger.info("Остановка сервисов...")
        for task in tasks:
            if not task.done():
                task.cancel()
        await stop_channel_service()
        await enrichment_worker.stop()
        await close_db()
        logger.info("Сервисы успешно остановлены.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass

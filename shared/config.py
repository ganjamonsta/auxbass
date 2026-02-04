"""
TG Player - Shared Configuration
"""
import os
import warnings
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Bot
    bot_token: str
    bot_username: str = ""  # For Telegram Login Widget
    
    # Telegram Bot API URL (use local server to bypass 20MB limit)
    # Default: https://api.telegram.org (20MB download limit)
    # Local server: http://localhost:8081 (no limit)
    telegram_api_url: str = "https://api.telegram.org"
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./tg_player.db"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_url: str = "http://localhost:8000"
    
    # Mini App
    webapp_url: str = "http://localhost:5173"
    
    # Security
    # ВАЖНО: SECRET_KEY должен быть одинаковым между перезапусками!
    # Иначе все JWT токены станут невалидными и пользователей выкинет из аккаунтов.
    secret_key: str = "dev-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 30  # JWT token expiration
    
    # Last.fm API (for artist images)
    lastfm_api_key: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    
    # Предупреждение о дефолтном SECRET_KEY в production
    if settings.secret_key == "dev-secret-key":
        # Проверяем, запущено ли в Docker (признак production)
        if os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER"):
            warnings.warn(
                "\n⚠️  ВНИМАНИЕ: Используется дефолтный SECRET_KEY!\n"
                "   Это приведёт к выбросу пользователей из аккаунтов при перезапуске контейнера.\n"
                "   Установите SECRET_KEY в .env файле с постоянным случайным значением.\n"
                "   Пример: SECRET_KEY=$(openssl rand -hex 32)\n",
                UserWarning,
                stacklevel=2
            )
    
    return settings

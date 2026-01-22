"""
TG Player - Shared Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Bot
    bot_token: str
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./tg_player.db"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_url: str = "http://localhost:8000"
    
    # Mini App
    webapp_url: str = "http://localhost:5173"
    
    # Security
    secret_key: str = "dev-secret-key"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()

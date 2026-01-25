"""
TG Player - Test Configuration
Provides common fixtures and configuration for pytest
"""
import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

# Configure asyncio for pytest
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_telegram_user():
    """Mock Telegram user data"""
    return {
        "id": 123456789,
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser",
        "language_code": "ru",
    }


@pytest.fixture
def mock_track():
    """Mock track data"""
    return {
        "id": 1,
        "title": "Test Song",
        "artist": "Test Artist",
        "album": "Test Album",
        "duration": 180,
        "file_id": "AgACAgIAAxkBAAIBZ2abc123",
        "cover_url": None,
        "play_count": 42,
        "is_public": True,
    }


@pytest.fixture
def mock_playlist():
    """Mock playlist data"""
    return {
        "id": 1,
        "name": "Test Playlist",
        "description": "Test Description",
        "is_public": True,
        "is_auto_album": False,
        "is_auto_source": False,
        "track_count": 10,
        "total_duration": 1800,
    }


@pytest.fixture
def mock_db_session():
    """Mock async database session"""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_bot():
    """Mock Telegram bot"""
    bot = MagicMock()
    bot.send_message = AsyncMock()
    bot.send_audio = AsyncMock()
    bot.edit_message_text = AsyncMock()
    bot.answer_callback_query = AsyncMock()
    return bot

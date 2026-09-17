import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message, User, Chat

from bot.handlers.menu import _safe_edit_text, cb_stats_refresh


@pytest.mark.asyncio
async def test_safe_edit_text_success():
    msg = MagicMock(spec=Message)
    msg.edit_text = AsyncMock()

    result = await _safe_edit_text(msg, "New text")
    assert result is True
    msg.edit_text.assert_awaited_once_with("New text")


@pytest.mark.asyncio
async def test_safe_edit_text_message_not_modified():
    msg = MagicMock(spec=Message)
    msg.edit_text = AsyncMock(
        side_effect=TelegramBadRequest(
            method="editMessageText",
            message="Bad Request: message is not modified: specified new message content and reply markup are exactly the same",
        )
    )

    result = await _safe_edit_text(msg, "Same text")
    assert result is False


@pytest.mark.asyncio
async def test_safe_edit_text_other_bad_request_raises():
    msg = MagicMock(spec=Message)
    msg.edit_text = AsyncMock(
        side_effect=TelegramBadRequest(
            method="editMessageText",
            message="Bad Request: chat not found",
        )
    )

    with pytest.raises(TelegramBadRequest) as exc_info:
        await _safe_edit_text(msg, "New text")
    assert "chat not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_cb_stats_refresh_not_modified(monkeypatch):
    import bot.handlers.menu as menu_mod

    monkeypatch.setattr(menu_mod, "_get_stats_text", AsyncMock(return_value="📊 Stats: 10 tracks"))

    msg = MagicMock(spec=Message)
    msg.edit_text = AsyncMock(
        side_effect=TelegramBadRequest(
            method="editMessageText",
            message="Bad Request: message is not modified: specified new message content and reply markup are exactly the same",
        )
    )

    cb = MagicMock(spec=CallbackQuery)
    cb.from_user = User(id=123, is_bot=False, first_name="Test")
    cb.message = msg
    cb.answer = AsyncMock()

    await cb_stats_refresh(cb)
    cb.answer.assert_awaited_once_with("Данные актуальны!")


@pytest.mark.asyncio
async def test_cb_stats_refresh_modified(monkeypatch):
    import bot.handlers.menu as menu_mod

    monkeypatch.setattr(menu_mod, "_get_stats_text", AsyncMock(return_value="📊 Stats: 11 tracks"))

    msg = MagicMock(spec=Message)
    msg.edit_text = AsyncMock()

    cb = MagicMock(spec=CallbackQuery)
    cb.from_user = User(id=123, is_bot=False, first_name="Test")
    cb.message = msg
    cb.answer = AsyncMock()

    await cb_stats_refresh(cb)
    cb.answer.assert_awaited_once_with("Обновлено!")

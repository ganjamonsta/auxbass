"""
Tests for channel member handling, channel verification, and unavailable track reconciliation.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from api.schemas.common import UserStatusResponse, TelegramUser


def test_user_status_response_schema_with_error():
    user = TelegramUser(id=123, first_name="Test")
    resp = UserStatusResponse(
        user=user,
        has_channel=False,
        can_save=False,
        channel_info=None,
        error="Бот не имеет прав администратора в канале",
    )
    assert resp.has_channel is False
    assert resp.error == "Бот не имеет прав администратора в канале"


def test_user_status_response_schema_active():
    user = TelegramUser(id=123, first_name="Test")
    resp = UserStatusResponse(
        user=user,
        has_channel=True,
        can_save=True,
        channel_info={"channel_id": -10012345, "channel_title": "My Music"},
    )
    assert resp.has_channel is True
    assert resp.error is None
    assert resp.channel_info["channel_title"] == "My Music"


@pytest.mark.asyncio
async def test_reconcile_channel_tracks():
    from bot.services.channels.service import ChannelService
    ch_svc = ChannelService()

    # When user has no active channel, reconcile returns 0
    restored = await ch_svc.reconcile_channel_tracks(99999999)
    assert restored == 0

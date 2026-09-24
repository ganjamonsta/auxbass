"""
Tests for Telegram Desktop JSON Export Importer (Lazy Resolution).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy import select

from bot.services.importer import parse_telegram_export_json, channel_importer, ExportAudioItem
from shared.database import get_session
from shared.models import UserChannel, ChannelMessage, ChannelMessageStatus, Track, UserLibrary
from api.routers.player import get_telegram_file_path


def test_parse_telegram_export_json():
    sample_json = {
        "name": "My Audio Channel",
        "type": "public_channel",
        "id": 1234567890,
        "messages": [
            {
                "id": 1,
                "type": "message",
                "text": "Regular text message",
            },
            {
                "id": 2,
                "type": "message",
                "media_type": "audio_file",
                "file": "songs/artist - track.mp3",
                "mime_type": "audio/mpeg",
                "duration_seconds": 180,
                "title": "Track Title",
                "performer": "Artist Name",
            },
            {
                "id": 3,
                "type": "message",
                "file": "music/audio.flac",
                "mime_type": "audio/flac",
                "duration_seconds": 240,
                "title": "FLAC Song",
                "performer": "Lossless Band",
            }
        ]
    }

    ch_name, ch_id, audio_items = parse_telegram_export_json(sample_json)
    assert ch_name == "My Audio Channel"
    assert ch_id == -1001234567890
    assert len(audio_items) == 2
    assert audio_items[0].message_id == 2
    assert audio_items[0].title == "Track Title"
    assert audio_items[0].performer == "Artist Name"
    assert audio_items[1].message_id == 3
    assert audio_items[1].title == "FLAC Song"


@pytest.mark.asyncio
async def test_get_telegram_file_path_bypasses_lazy():
    """Verify that lazy and pending placeholders immediately return None without calling Telegram."""
    assert await get_telegram_file_path("lazy:-10012345:100") is None
    assert await get_telegram_file_path("pending:something") is None
    assert await get_telegram_file_path("") is None
    assert await get_telegram_file_path(None) is None


@pytest.mark.asyncio
async def test_import_from_json_lazy():
    import random
    suffix = random.randint(100000, 999999)
    test_user_id = 888000000 + suffix
    target_channel_id = -100900000000 - suffix
    msg_id_1 = suffix * 10 + 1
    msg_id_2 = suffix * 10 + 2

    # Setup active user channel in DB
    async with get_session() as session:
        ch = await session.scalar(select(UserChannel).where(UserChannel.user_id == test_user_id))
        if not ch:
            ch = UserChannel(
                user_id=test_user_id,
                channel_id=target_channel_id,
                channel_title="Test Music Channel",
                is_active=True,
            )
            session.add(ch)
            await session.commit()

    sample_json = {
        "name": "Test Music Channel",
        "id": abs(target_channel_id) - 1000000000000,
        "messages": [
            {
                "id": msg_id_1,
                "media_type": "audio_file",
                "file": "track1.mp3",
                "title": "Lazy Song 1",
                "performer": "Lazy Artist",
                "duration_seconds": 200,
            },
            {
                "id": msg_id_2,
                "media_type": "audio_file",
                "file": "track2.mp3",
                "title": "Lazy Song 2",
                "performer": "Lazy Artist",
                "duration_seconds": 210,
            }
        ]
    }

    mock_bot = MagicMock()
    # Import using ChannelImporter
    result = await channel_importer.import_from_json(
        user_id=test_user_id,
        json_data=sample_json,
        bot=mock_bot,
    )

    assert result["success"] is True
    assert result["imported"] == 2
    assert result["skipped"] == 0

    # Verify tracks created with lazy file_ids
    async with get_session() as session:
        t1 = await session.scalar(
            select(Track).where(Track.file_unique_id == f"lazy_{target_channel_id}_{msg_id_1}")
        )
        assert t1 is not None
        assert t1.file_id == f"lazy:{target_channel_id}:{msg_id_1}"
        assert t1.title == "Lazy Song 1"
        assert t1.artist == "Lazy Artist"

        # Check ChannelMessage link
        cm = await session.scalar(
            select(ChannelMessage).where(ChannelMessage.track_id == t1.id)
        )
        assert cm is not None
        assert cm.message_id == msg_id_1
        assert cm.status == ChannelMessageStatus.SENT

        # Check UserLibrary
        ul = await session.scalar(
            select(UserLibrary).where(UserLibrary.user_id == test_user_id, UserLibrary.track_id == t1.id)
        )
        assert ul is not None

    # Test idempotence / skipping already imported tracks
    result2 = await channel_importer.import_from_json(
        user_id=test_user_id,
        json_data=sample_json,
        bot=mock_bot,
    )
    assert result2["success"] is True
    assert result2["imported"] == 0
    assert result2["skipped"] == 2

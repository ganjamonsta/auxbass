"""
Tests for playlist operations: update, cover upload/deletion, public list, and get_playlist_info unpacking.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import pytest_asyncio

from shared.models import Base, User, Playlist, Track, PlaylistTrack
from api.schemas.common import TelegramUser
from api.schemas.playlists import PlaylistUpdate
from api.routers.playlists import (
    get_playlist_info,
    update_playlist,
    upload_playlist_cover,
    delete_playlist_cover,
    get_public_playlists,
)

SAMPLE_JPEG_BYTES = (
    b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00'
    b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t'
    b'\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
    b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' \",#\x1c\x1c(7),01444\x1f\'9=82<.342'
    b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f'
    b'\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00'
    b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01'
    b'\x00\x00?\x00\xbf\x00\xff\xd9'
)


@pytest_asyncio.fixture
async def playlist_test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with session_maker() as session:
        user = User(id=100, username="test_owner", first_name="TestOwner")
        session.add(user)
        await session.commit()

        playlist = Playlist(
            id=1,
            owner_id=100,
            name="My Awesome Playlist",
            description="Test description",
            is_public=True,
        )
        session.add(playlist)

        track1 = Track(
            id=1,
            file_id="tg_1",
            file_unique_id="u_1",
            title="Track 1",
            artist="Artist 1",
            duration=120,
            uploader_id=100,
            is_unavailable=False,
        )
        track2 = Track(
            id=2,
            file_id="tg_2",
            file_unique_id="u_2",
            title="Track 2",
            artist="Artist 2",
            duration=180,
            uploader_id=100,
            is_unavailable=True,
        )
        session.add_all([track1, track2])
        await session.commit()

        pt1 = PlaylistTrack(playlist_id=1, track_id=1, position=0)
        pt2 = PlaylistTrack(playlist_id=1, track_id=2, position=1)
        session.add_all([pt1, pt2])
        await session.commit()

    async with session_maker() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_playlist_info_returns_five_values(playlist_test_db):
    result = await get_playlist_info(playlist_test_db, 1)
    assert len(result) == 5
    track_count, total_duration, unavailable_count, cover_url, covers = result
    assert track_count == 2
    assert total_duration == 300
    assert unavailable_count == 1


@pytest.mark.asyncio
async def test_update_playlist_unpacks_correctly(playlist_test_db):
    user = TelegramUser(id=100, username="test_owner", first_name="TestOwner")
    update_data = PlaylistUpdate(name="Renamed Playlist", description="New description")

    resp = await update_playlist(1, update_data, user=user, db=playlist_test_db)
    assert resp.name == "Renamed Playlist"
    assert resp.track_count == 2
    assert resp.unavailable_track_count == 1
    assert resp.total_duration == 300
    assert resp.is_owner is True
    assert resp.owner_id == 100


@pytest.mark.asyncio
async def test_upload_and_delete_playlist_cover(playlist_test_db):
    user = TelegramUser(id=100, username="test_owner", first_name="TestOwner")

    mock_bot = MagicMock()
    mock_sent = MagicMock()
    mock_photo = MagicMock()
    mock_photo.file_id = "cover_photo_file_123"
    mock_sent.photo = [mock_photo]
    mock_bot.send_photo = AsyncMock(return_value=mock_sent)

    import io
    file = UploadFile(file=io.BytesIO(SAMPLE_JPEG_BYTES), filename="cover.jpg", headers={"content-type": "image/jpeg"})

    with patch("api.routers.playlists._get_bot", return_value=mock_bot):
        res = await upload_playlist_cover(1, file=file, user=user, db=playlist_test_db)

    assert res["status"] == "success"
    assert res["custom_cover_url"] == "/api/images/cover_photo_file_123"
    assert res["cover_url"] == "/api/images/cover_photo_file_123"

    del_res = await delete_playlist_cover(1, user=user, db=playlist_test_db)
    assert del_res["status"] == "deleted"
    assert del_res["custom_cover_url"] is None


@pytest.mark.asyncio
async def test_get_public_playlists_unpacks_correctly(playlist_test_db):
    user = TelegramUser(id=100, username="test_owner", first_name="TestOwner")
    res = await get_public_playlists(page=1, per_page=10, user=user, db=playlist_test_db)
    assert res.total >= 1
    pl = res.items[0]
    assert pl.id == 1
    assert pl.unavailable_track_count == 1

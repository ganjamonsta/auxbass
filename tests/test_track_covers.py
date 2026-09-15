"""
Tests for track cover editing, suggestions, upload, and deletion.
"""
import io
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from shared.models import (
    Base, User, Track, UserLibrary, TrackEnrichment,
    EnrichmentStatus, LibrarySource
)
from shared.matching import normalize_artist
from api.schemas.tracks import SetCoverRequest
from api.schemas.common import TelegramUser
from api.routers.tracks import (
    get_track_cover_suggestions,
    set_track_cover,
    upload_track_cover,
    delete_track_cover,
)
import pytest_asyncio


# Valid 1x1 JPEG minimal bytes
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
async def cover_test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with session_maker() as session:
        user_uploader = User(id=100, username="uploader")
        user_lib_owner = User(id=200, username="lib_owner")
        user_stranger = User(id=300, username="stranger")
        session.add_all([user_uploader, user_lib_owner, user_stranger])
        await session.commit()

        track = Track(
            id=1,
            file_id="tg_file_123",
            file_unique_id="unique_123",
            title="Blinding Lights",
            artist="The Weeknd",
            normalized_artist=normalize_artist("The Weeknd"),
            duration=200,
            uploader_id=100,
            enrichment_status=EnrichmentStatus.COMPLETED,
        )
        session.add(track)
        await session.commit()

        lib_entry = UserLibrary(
            user_id=200,
            track_id=1,
            source=LibrarySource.SHARED,
        )
        session.add(lib_entry)
        await session.commit()

    yield session_maker
    await engine.dispose()


@pytest.mark.asyncio
async def test_get_track_cover_suggestions(cover_test_db):
    """Test getting cover suggestions for a track."""
    user_100 = TelegramUser(id=100, first_name="Uploader")

    async with cover_test_db() as session:
        mock_candidates = [
            {
                "id": "itunes_123",
                "cover_url": "https://is1-ssl.mzstatic.com/image/thumb/xyz/1000x1000bb.jpg",
                "thumbnail_url": "https://is1-ssl.mzstatic.com/image/thumb/xyz/300x300bb.jpg",
                "source": "itunes",
                "title": "Blinding Lights",
                "artist": "The Weeknd",
                "album": "After Hours",
                "year": "2020",
                "width": 1000,
                "height": 1000,
            }
        ]
        with patch("api.routers.tracks.search_cover_suggestions", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_candidates
            res = await get_track_cover_suggestions(
                track_id=1,
                query=None,
                user=user_100,
                db=session,
            )

        assert len(res) == 1
        assert res[0].source == "itunes"
        assert res[0].album == "After Hours"
        mock_search.assert_called_once_with("The Weeknd Blinding Lights", limit_per_source=8)


@pytest.mark.asyncio
async def test_set_track_cover_from_proxy_url(cover_test_db):
    """Test setting cover with an existing proxy URL (/api/images/...)."""
    user_100 = TelegramUser(id=100, first_name="Uploader")

    async with cover_test_db() as session:
        data = SetCoverRequest(cover_url="/api/images/existing_file_id")
        res = await set_track_cover(
            track_id=1,
            data=data,
            user=user_100,
            db=session,
        )

        assert res.cover_url == "/api/images/existing_file_id"
        db_track = await session.get(Track, 1)
        assert db_track.enrichment.cover_url == "/api/images/existing_file_id"
        assert db_track.enrichment_status == EnrichmentStatus.COMPLETED


@pytest.mark.asyncio
async def test_set_track_cover_from_external_url(cover_test_db):
    """Test downloading an external cover URL and uploading it to Telegram."""
    user_200 = TelegramUser(id=200, first_name="LibOwner")  # Has track in library

    async with cover_test_db() as session:
        # Mock HTTP download
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read = AsyncMock(return_value=SAMPLE_JPEG_BYTES)
        
        mock_get_context = MagicMock()
        mock_get_context.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_get_context.__aexit__ = AsyncMock(return_value=None)
        
        mock_http_session = MagicMock()
        mock_http_session.get.return_value = mock_get_context

        # Mock Bot send_photo
        mock_photo = MagicMock()
        mock_photo.file_id = "tg_generated_file_456"
        mock_msg = MagicMock()
        mock_msg.photo = [mock_photo]

        mock_bot = MagicMock()
        mock_bot.send_photo = AsyncMock(return_value=mock_msg)

        with patch("api.routers.tracks.get_http_session", AsyncMock(return_value=mock_http_session)), \
             patch("api.routers.tracks._get_bot", return_value=mock_bot):
            
            data = SetCoverRequest(cover_url="https://is1-ssl.mzstatic.com/image/thumb/xyz/1000x1000bb.jpg")
            res = await set_track_cover(
                track_id=1,
                data=data,
                user=user_200,
                db=session,
            )

        assert res.cover_url == "/api/images/tg_generated_file_456"
        db_track = await session.get(Track, 1)
        assert db_track.enrichment.cover_url == "/api/images/tg_generated_file_456"


@pytest.mark.asyncio
async def test_upload_track_cover_file(cover_test_db):
    """Test uploading a custom cover file directly."""
    user_100 = TelegramUser(id=100, first_name="Uploader")

    async with cover_test_db() as session:
        mock_photo = MagicMock()
        mock_photo.file_id = "tg_custom_upload_789"
        mock_msg = MagicMock()
        mock_msg.photo = [mock_photo]

        mock_bot = MagicMock()
        mock_bot.send_photo = AsyncMock(return_value=mock_msg)

        upload_file = UploadFile(
            file=io.BytesIO(SAMPLE_JPEG_BYTES),
            filename="my_cover.jpg",
            headers={"content-type": "image/jpeg"},
        )

        with patch("api.routers.tracks._get_bot", return_value=mock_bot):
            res = await upload_track_cover(
                track_id=1,
                file=upload_file,
                user=user_100,
                db=session,
            )

        assert res.cover_url == "/api/images/tg_custom_upload_789"


@pytest.mark.asyncio
async def test_delete_track_cover(cover_test_db):
    """Test deleting track cover."""
    user_100 = TelegramUser(id=100, first_name="Uploader")

    async with cover_test_db() as session:
        # First set a cover
        db_track = await session.get(Track, 1)
        db_track.enrichment = TrackEnrichment(track_id=1, cover_url="/api/images/old_cover")
        await session.commit()

        res = await delete_track_cover(
            track_id=1,
            user=user_100,
            db=session,
        )

        assert res.cover_url is None
        reloaded = await session.get(Track, 1)
        assert reloaded.enrichment.cover_url is None


@pytest.mark.asyncio
async def test_cover_permission_denied_for_stranger(cover_test_db):
    """Test that a user without the track in library cannot modify its cover."""
    user_300 = TelegramUser(id=300, first_name="Stranger")

    async with cover_test_db() as session:
        data = SetCoverRequest(cover_url="/api/images/some_file")
        with pytest.raises(HTTPException) as exc_info:
            await set_track_cover(
                track_id=1,
                data=data,
                user=user_300,
                db=session,
            )
        assert exc_info.value.status_code == 403

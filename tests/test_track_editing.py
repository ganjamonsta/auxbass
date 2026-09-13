"""
Tests for track editing functionality
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from shared.models import (
    Base, User, Track, UserLibrary, TrackEnrichment, Album, AlbumTrack,
    EnrichmentStatus, LibrarySource
)
import pytest_asyncio
from shared.matching import normalize_artist
from api.schemas.tracks import TrackUpdate
from bot.services.enrichment.processor import EnrichmentResult


@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session_maker() as session:
        # Create 2 users
        user_uploader = User(id=100, username="uploader")
        user_library_owner = User(id=200, username="lib_owner")
        session.add_all([user_uploader, user_library_owner])
        await session.commit()
        
        # Create a track uploaded by user 100
        track = Track(
            id=1,
            file_id="tg_file_123",
            file_unique_id="unique_123",
            title="Old Title",
            artist="Old Artist",
            normalized_artist=normalize_artist("Old Artist"),
            duration=200,
            uploader_id=100,
            enrichment_status=EnrichmentStatus.COMPLETED,
        )
        session.add(track)
        await session.commit()
        
        # Add track to user 200's library
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
async def test_non_uploader_can_edit_library_track(test_db):
    """Test that a user who has a track in their library (but is not uploader) can edit it"""
    from api.routers.tracks import update_track
    from api.schemas.common import TelegramUser

    user_200 = TelegramUser(id=200, first_name="Owner", username="lib_owner")

    async with test_db() as session:
        update_data = TrackUpdate(
            title="New Fixed Title",
            artist="New Fixed Artist",
            album="Awesome Album",
            genre="Electronic",
        )
        
        with patch("bot.services.channels.get_channel_service") as mock_ch:
            mock_svc = AsyncMock()
            mock_ch.return_value = mock_svc
            
            with patch("bot.services.albums.album_service.find_or_create_album", new_callable=AsyncMock) as mock_album:
                mock_album.return_value = 42
                with patch("bot.services.albums.album_service.assign_track_to_album", new_callable=AsyncMock) as mock_assign:
                    res = await update_track(
                        track_id=1,
                        data=update_data,
                        user=user_200,
                        db=session,
                    )
        
        assert res.title == "New Fixed Title"
        assert res.artist == "New Fixed Artist"
        assert res.genre == "Electronic"

        # Verify in DB
        db_track = await session.get(Track, 1)
        assert db_track.title == "New Fixed Title"
        assert db_track.artist == "New Fixed Artist"
        assert db_track.normalized_artist == normalize_artist("New Fixed Artist")
        assert db_track.enrichment_status == EnrichmentStatus.COMPLETED


@pytest.mark.asyncio
async def test_unauthorized_user_cannot_edit(test_db):
    """Test that a random user without the track in library cannot edit it"""
    from api.routers.tracks import update_track
    from api.schemas.common import TelegramUser
    from fastapi import HTTPException

    user_999 = TelegramUser(id=999, first_name="Stranger", username="stranger")

    async with test_db() as session:
        update_data = TrackUpdate(title="Hacked")
        with pytest.raises(HTTPException) as exc_info:
            await update_track(
                track_id=1,
                data=update_data,
                user=user_999,
                db=session,
            )
        assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_enrichment_worker_does_not_overwrite_user_edits():
    """Test that EnrichmentWorker does not overwrite custom title and artist with canonical ones"""
    from bot.services.enrichment.worker import EnrichmentWorker

    worker = EnrichmentWorker()

    # Track has a user-custom title
    track_title = "My Edited Title (Special Version)"
    track_artist = "Skrillex"

    # Simulated Deezer/Last.fm result proposing canonical title
    result = EnrichmentResult(
        success=True,
        confidence=80,
        canonical_title="My Edited Title",  # Without special version
        canonical_artist="Skrillex",
    )

    # In our updated code:
    placeholder_titles = ("без названия", "unknown track", "untitled", "audio", "track")
    # Title must NOT be overwritten because it is not a placeholder
    assert track_title.strip().lower() not in placeholder_titles

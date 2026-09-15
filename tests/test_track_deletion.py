"""
Tests for track deletion and orphan cleanup in database
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from shared.models import (
    Base, User, Track, UserLibrary, LibrarySource, EnrichmentStatus
)
from shared.matching import normalize_artist
from api.routers.tracks import delete_track
from api.schemas.common import TelegramUser


@pytest_asyncio.fixture
async def deletion_test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session_maker() as session:
        u1 = User(id=100, username="user1")
        u2 = User(id=200, username="user2")
        session.add_all([u1, u2])

        # Track 1: Only user 100 has it
        t1 = Track(
            id=1,
            file_id="fid_1",
            file_unique_id="fuid_1",
            title="Solo Track",
            artist="Artist 1",
            normalized_artist="artist 1",
            duration=180,
            uploader_id=100,
            enrichment_status=EnrichmentStatus.COMPLETED,
        )
        # Track 2: Both user 100 and user 200 have it
        t2 = Track(
            id=2,
            file_id="fid_2",
            file_unique_id="fuid_2",
            title="Shared Track",
            artist="Artist 2",
            normalized_artist="artist 2",
            duration=210,
            uploader_id=100,
            enrichment_status=EnrichmentStatus.COMPLETED,
        )
        session.add_all([t1, t2])
        await session.flush()

        session.add_all([
            UserLibrary(user_id=100, track_id=1, source=LibrarySource.UPLOADED),
            UserLibrary(user_id=100, track_id=2, source=LibrarySource.UPLOADED),
            UserLibrary(user_id=200, track_id=2, source=LibrarySource.SHARED),
        ])
        await session.commit()

    yield session_maker
    await engine.dispose()


@pytest.mark.asyncio
async def test_delete_track_purges_orphaned_global_track(deletion_test_db):
    user = TelegramUser(id=100, username="user1", first_name="User")

    with patch("api.routers.tracks.get_channel_service") as mock_ch:
        mock_svc = AsyncMock()
        mock_svc.delete_track_from_channel.return_value = True
        mock_ch.return_value = mock_svc

        async with deletion_test_db() as session:
            res = await delete_track(track_id=1, force_purge=False, user=user, db=session)
            assert res["status"] == "deleted"
            assert res["purged_from_global"] is True

            # Assert Track 1 is completely purged from tracks table
            t = await session.get(Track, 1)
            assert t is None

            # Assert UserLibrary is removed
            lib = await session.execute(select(UserLibrary).where(UserLibrary.track_id == 1))
            assert lib.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_track_keeps_global_track_if_other_users_exist(deletion_test_db):
    user = TelegramUser(id=100, username="user1", first_name="User")

    with patch("api.routers.tracks.get_channel_service") as mock_ch:
        mock_svc = AsyncMock()
        mock_svc.delete_track_from_channel.return_value = True
        mock_ch.return_value = mock_svc

        async with deletion_test_db() as session:
            res = await delete_track(track_id=2, force_purge=False, user=user, db=session)
            assert res["status"] == "deleted"
            assert res["purged_from_global"] is False

            # Assert Track 2 still exists because user 200 has it
            t = await session.get(Track, 2)
            assert t is not None

            # User 100's library entry is gone
            u1_lib = await session.execute(
                select(UserLibrary).where(UserLibrary.track_id == 2, UserLibrary.user_id == 100)
            )
            assert u1_lib.scalar_one_or_none() is None

            # User 200's library entry remains
            u2_lib = await session.execute(
                select(UserLibrary).where(UserLibrary.track_id == 2, UserLibrary.user_id == 200)
            )
            assert u2_lib.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_delete_track_force_purge_removes_from_all(deletion_test_db):
    user = TelegramUser(id=100, username="user1", first_name="User")

    with patch("api.routers.tracks.get_channel_service") as mock_ch:
        mock_svc = AsyncMock()
        mock_svc.delete_track_from_channel.return_value = True
        mock_ch.return_value = mock_svc

        async with deletion_test_db() as session:
            res = await delete_track(track_id=2, force_purge=True, user=user, db=session)
            assert res["status"] == "deleted"
            assert res["purged_from_global"] is True

            # Track 2 is completely gone
            t = await session.get(Track, 2)
            assert t is None

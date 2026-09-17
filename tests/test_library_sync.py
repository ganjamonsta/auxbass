"""
Unit tests for library synchronization and pagination functionality.
"""
import pytest
from datetime import datetime, timedelta, timezone
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from shared.models import (
    Base, User, Track, UserLibrary, TrackEnrichment, Album, AlbumTrack,
    EnrichmentStatus, LibrarySource, utcnow
)
from shared.matching import normalize_artist
from api.schemas.common import TelegramUser
from api.routers.library import get_my_tracks, get_library_sync_state


@pytest_asyncio.fixture
async def sync_test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session_maker() as session:
        user = User(id=888, username="test_user")
        session.add(user)
        await session.commit()
        
        # Create 5 tracks in user's library
        now = utcnow()
        for i in range(1, 6):
            track = Track(
                id=i,
                file_id=f"tg_file_{i}",
                file_unique_id=f"unique_{i}",
                title=f"Track {i}",
                artist=f"Artist {i % 2 + 1}",
                normalized_artist=normalize_artist(f"Artist {i % 2 + 1}"),
                duration=180 + i,
                uploader_id=888,
                enrichment_status=EnrichmentStatus.COMPLETED,
                created_at=now - timedelta(minutes=10 - i),
                updated_at=now - timedelta(minutes=10 - i),
            )
            session.add(track)
            await session.flush()
            
            lib = UserLibrary(
                user_id=888,
                track_id=i,
                source=LibrarySource.UPLOADED,
                added_at=now - timedelta(minutes=10 - i),
            )
            session.add(lib)
        await session.commit()
    
    yield session_maker
    await engine.dispose()


@pytest.mark.asyncio
async def test_get_my_tracks_offset_pagination(sync_test_db):
    """Test offset and limit pagination for get_my_tracks"""
    user = TelegramUser(id=888, first_name="Tester")
    
    async with sync_test_db() as session:
        # Page 1 using offset 0, limit 2
        res1 = await get_my_tracks(
            offset=0,
            limit=2,
            user=user,
            db=session,
        )
        assert res1.total == 5
        assert len(res1.items) == 2
        assert res1.offset == 0
        assert res1.limit == 2
        assert res1.items[0].id == 5  # added_at desc: track 5 is newest
        assert res1.items[1].id == 4

        # Page 2 using offset 2, limit 2
        res2 = await get_my_tracks(
            offset=2,
            limit=2,
            user=user,
            db=session,
        )
        assert res2.total == 5
        assert len(res2.items) == 2
        assert res2.offset == 2
        assert res2.items[0].id == 3
        assert res2.items[1].id == 2


@pytest.mark.asyncio
async def test_get_library_sync_state(sync_test_db):
    """Test get_library_sync_state returns latest track info and updated tracks"""
    user = TelegramUser(id=888, first_name="Tester")
    
    async with sync_test_db() as session:
        sync_res = await get_library_sync_state(
            user=user,
            db=session,
        )
        assert sync_res.total_tracks == 5
        assert sync_res.last_track_id == 5
        assert sync_res.last_added_at is not None
        assert sync_res.last_updated_at is not None
        assert sync_res.stats.artist_count == 2
        assert sync_res.updated_tracks == []


@pytest.mark.asyncio
async def test_get_library_sync_state_with_since(sync_test_db):
    """Test get_library_sync_state filters updated_tracks by since timestamp"""
    user = TelegramUser(id=888, first_name="Tester")
    
    async with sync_test_db() as session:
        # Update track 5 metadata and updated_at
        track5 = await session.get(Track, 5)
        track5.title = "Enriched Salt"
        track5.updated_at = utcnow()
        await session.commit()
        
        # Query with since = 20 seconds ago
        since_time = utcnow() - timedelta(seconds=10)
        sync_res = await get_library_sync_state(
            since=since_time,
            user=user,
            db=session,
        )
        assert len(sync_res.updated_tracks) >= 1
        assert sync_res.updated_tracks[0].id == 5
        assert sync_res.updated_tracks[0].title == "Enriched Salt"

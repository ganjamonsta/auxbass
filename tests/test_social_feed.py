import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from shared.models import Base, User, UserFollow, Track
from api.routers.social import get_social_feed
from api.schemas.common import TelegramUser


@pytest.mark.asyncio
async def test_social_feed_endpoints():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # Create users: viewer, friend, stranger, hidden_user
        viewer = User(id=1, username="viewer", first_name="Viewer")
        friend = User(id=2, username="friend_alex", first_name="Alex", custom_nickname="DJ Alex")
        stranger = User(id=3, username="stranger_bob", first_name="Bob")
        hidden_user = User(id=4, username="ghost", first_name="Ghost", hide_profile=True)
        
        session.add_all([viewer, friend, stranger, hidden_user])
        await session.commit()

        # Viewer follows friend (id=2)
        follow = UserFollow(follower_id=1, following_id=2)
        session.add(follow)
        await session.commit()

        # Add tracks
        t1 = Track(
            id=101,
            file_id="tg_101",
            file_unique_id="uniq_101",
            title="Friend Track 1",
            artist="DJ Alex",
            uploader_id=2,
            is_public=True,
            is_unavailable=False,
            created_at=datetime(2026, 9, 13, 12, 0, 0)
        )
        t2 = Track(
            id=102,
            file_id="tg_102",
            file_unique_id="uniq_102",
            title="Stranger Track 1",
            artist="Bob The Builder",
            uploader_id=3,
            is_public=True,
            is_unavailable=False,
            created_at=datetime(2026, 9, 13, 13, 0, 0)
        )
        t3 = Track(
            id=103,
            file_id="tg_103",
            file_unique_id="uniq_103",
            title="Hidden User Track",
            artist="Secret",
            uploader_id=4,
            is_public=True,
            is_unavailable=False,
            created_at=datetime(2026, 9, 13, 14, 0, 0)
        )
        session.add_all([t1, t2, t3])
        await session.commit()

        tg_viewer = TelegramUser(id=1, first_name="Viewer", username="viewer")

        # 1. Test following feed
        res_following = await get_social_feed(scope="following", page=1, per_page=10, user=tg_viewer, db=session)
        assert res_following["total"] == 1
        assert len(res_following["items"]) == 1
        item = res_following["items"][0]
        assert item["id"] == 101
        assert item["title"] == "Friend Track 1"
        assert item["uploader"]["id"] == 2
        assert item["uploader"]["display_name"] == "DJ Alex"
        assert item["uploader"]["username"] == "friend_alex"

        # 2. Test global feed (should include friend and stranger, but NOT hidden_user)
        res_global = await get_social_feed(scope="global", page=1, per_page=10, user=tg_viewer, db=session)
        assert res_global["total"] == 2
        assert len(res_global["items"]) == 2
        titles = [it["title"] for it in res_global["items"]]
        assert "Stranger Track 1" in titles
        assert "Friend Track 1" in titles
        assert "Hidden User Track" not in titles

        # 3. Test empty following feed for stranger (who follows no one)
        tg_stranger = TelegramUser(id=3, first_name="Bob", username="stranger_bob")
        res_empty = await get_social_feed(scope="following", page=1, per_page=10, user=tg_stranger, db=session)
        assert res_empty["total"] == 0
        assert len(res_empty["items"]) == 0
        assert res_empty["has_more"] is False

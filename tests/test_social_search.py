import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from shared.models import Base, User
from api.routers.social import search_users
from api.schemas.common import TelegramUser


@pytest.mark.asyncio
async def test_search_users_endpoints():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # Current searching user
        me = User(id=1, username="current_user", first_name="Me", last_name="Self")
        # Target user
        target = User(id=2, username="Pivovar228", first_name="Кира", last_name="Пивоваров")
        # Hidden user
        hidden = User(id=3, username="secret_pivovar", first_name="Кира", last_name="Скрытый", hide_from_search=True)
        
        session.add_all([me, target, hidden])
        await session.commit()

        current_tg_user = TelegramUser(id=1, first_name="Me", username="current_user")

        # 1. Search with parameter `query`
        res = await search_users(query="Pivovar228", user=current_tg_user, db=session)
        assert res.total == 1
        assert res.items[0].username == "Pivovar228"

        # 2. Search with parameter `q`
        res = await search_users(q="Pivovar228", user=current_tg_user, db=session)
        assert res.total == 1
        assert res.items[0].username == "Pivovar228"

        # 3. Search with leading '@' symbol
        res = await search_users(query="@Pivovar228", user=current_tg_user, db=session)
        assert res.total == 1
        assert res.items[0].username == "Pivovar228"

        # 4. Search by first name
        res = await search_users(query="Кира", user=current_tg_user, db=session)
        assert res.total == 1
        assert res.items[0].id == 2  # hidden user is excluded

        # 5. Search by full name "Кира Пивоваров"
        res = await search_users(query="Кира Пивоваров", user=current_tg_user, db=session)
        assert res.total == 1
        assert res.items[0].id == 2

        # 6. Search for self should return 0
        res = await search_users(query="current_user", user=current_tg_user, db=session)
        assert res.total == 0

        # 7. Short query (< 2 chars) should safely return empty
        res = await search_users(query="a", user=current_tg_user, db=session)
        assert res.total == 0

        # 8. User with custom nickname and hide_telegram_id
        custom_user = User(
            id=4,
            username="secret_tg_name",
            first_name="Иван",
            last_name="Иванов",
            custom_nickname="CyberDemon",
            custom_avatar_url="/api/avatars/avatar_4.jpg",
            hide_telegram_id=True,
        )
        session.add(custom_user)
        await session.commit()

        # Search by custom nickname
        res = await search_users(query="CyberDemon", user=current_tg_user, db=session)
        assert res.total == 1
        item = res.items[0]
        assert item.id == 4
        assert item.display_name == "CyberDemon"
        assert item.avatar_url == "/api/avatars/avatar_4.jpg"
        # Since hide_telegram_id is True and current_user != 4, username must be hidden
        assert item.username is None
        assert item.hide_telegram_id is True

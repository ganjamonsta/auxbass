"""
TG Player - Database Session Manager v2

Supports both SQLite and PostgreSQL with proper connection pooling.
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from .config import get_settings
from .models import Base


settings = get_settings()


def get_database_url() -> str:
    """
    Get database URL, converting to async driver if needed.
    
    Supports:
    - sqlite:// -> sqlite+aiosqlite://
    - postgresql:// -> postgresql+asyncpg://
    """
    url = settings.database_url
    
    # Convert to async drivers
    if url.startswith("sqlite://"):
        url = url.replace("sqlite://", "sqlite+aiosqlite://")
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://")
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://")
    
    return url


# Determine database type and pool settings
database_url = get_database_url()
is_sqlite = "sqlite" in database_url

# Build engine kwargs based on database type
engine_kwargs = {
    "echo": False,  # Set True for SQL debugging
}

if is_sqlite:
    # SQLite: use NullPool, no pool settings
    engine_kwargs["poolclass"] = NullPool
else:
    # PostgreSQL: use connection pooling for better performance
    engine_kwargs.update({
        "pool_size": 10,           # Base pool size
        "max_overflow": 20,        # Extra connections when busy
        "pool_timeout": 30,        # Seconds to wait for connection
        "pool_recycle": 1800,      # Recycle connections after 30 min
        "pool_pre_ping": True,     # Test connections before use
    })

# Create async engine
engine = create_async_engine(database_url, **engine_kwargs)

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    """Drop all database tables (use with caution!)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def close_db():
    """Close database connections"""
    await engine.dispose()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session context manager.
    Automatically commits on success, rollbacks on exception.
    
    Usage:
        async with get_session() as session:
            result = await session.execute(query)
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI.
    
    Usage:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ============== Transaction Helpers ==============

@asynccontextmanager
async def transaction():
    """
    Explicit transaction context.
    Commit is manual - you need to call session.commit().
    
    Usage:
        async with transaction() as session:
            session.add(obj1)
            session.add(obj2)
            await session.commit()  # Commits both
    """
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

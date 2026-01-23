"""
TG Player - Database Session Manager
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from .config import get_settings
from .models import Base


settings = get_settings()

# Determine pool settings based on database type
# SQLite doesn't support connection pooling well
is_sqlite = settings.database_url.startswith("sqlite")

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
engine = create_async_engine(settings.database_url, **engine_kwargs)

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


async def close_db():
    """Close database connections"""
    await engine.dispose()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session context manager"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

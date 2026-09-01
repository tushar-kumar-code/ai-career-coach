from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings

def get_clean_db_url(url: str) -> str:
    if not url:
        return "sqlite+aiosqlite:///./aicareercoach.db"
    url_str = str(url).strip()
    if url_str.startswith("postgres://"):
        url_str = url_str.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url_str.startswith("postgresql://") and not url_str.startswith("postgresql+asyncpg://"):
        url_str = url_str.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url_str

# Create async engine for SQLite / PostgreSQL / Supabase connection
engine = create_async_engine(
    get_clean_db_url(settings.DATABASE_URL),
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

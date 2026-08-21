"""
conftest.py -- shared test fixtures for AI Career Coach backend test suite.
Ensures all database tables are created before any test runs.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import engine, Base
import app.models  # noqa: F401 -- ensures all models registered with Base


@pytest.fixture(scope="session", autouse=True)
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
async def create_tables():
    """Create all database tables once before any test runs."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Optionally drop all tables after full suite (not done here to preserve existing behavior)

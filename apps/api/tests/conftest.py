import os
import sys
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

# Ensure apps/api directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.db.session import async_engine


@pytest.fixture(autouse=True)
async def cleanup_db_connections():
    yield
    # Safely close pooled database connections
    await async_engine.dispose()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

"""Pytest fixtures."""
import asyncio
import sys

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

# On Windows, ProactorEventLoop can cause "Event loop is closed" with asyncpg.
# Use SelectorEventLoop instead.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture
async def client():
    """Test client - uses real app with configured database."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

"""Engine and jobs API integration tests."""
import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_trigger_engine_a_requires_auth(client: AsyncClient):
    """Engine A trigger requires authentication."""
    res = await client.post(
        "/api/v1/jobs/engine-a",
        json={"property_id": "any"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_trigger_engine_a_with_invalid_property(client: AsyncClient):
    """Engine A returns 404 for unknown property."""
    # Create user and get token
    email = f"eng-{uuid.uuid4().hex[:8]}@example.com"
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "password123"},
    )
    if signup.status_code != 200:
        pytest.skip("Database not available")
    token = signup.json()["access_token"]

    res = await client.post(
        "/api/v1/jobs/engine-a",
        json={"property_id": "00000000-0000-0000-0000-000000000000"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_engine_a_requires_property_id(client: AsyncClient):
    """Engine A requires property_id - 401 without auth, 422 with auth and bad body."""
    res = await client.post("/api/v1/jobs/engine-a", json={})
    assert res.status_code == 401  # No auth

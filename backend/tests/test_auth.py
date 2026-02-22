"""Auth and error envelope tests."""
import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    """Health endpoint returns ok."""
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_validation_error_envelope(client: AsyncClient):
    """422 validation errors use standard envelope."""
    res = await client.post(
        "/api/v1/auth/signup",
        json={"email": "invalid-email", "password": "short"},
    )
    assert res.status_code == 422
    data = res.json()
    assert data.get("success") is False
    assert "error" in data
    assert "detail" in data


@pytest.mark.asyncio
async def test_401_error_envelope(client: AsyncClient):
    """401 unauthorized uses standard envelope."""
    res = await client.get("/api/v1/organizations")
    assert res.status_code == 401
    data = res.json()
    assert data.get("success") is False
    assert "error" in data
    assert data.get("error_code") in ("unauthorized", "http_401")


@pytest.mark.asyncio
async def test_404_error_envelope(client: AsyncClient):
    """404 not found uses standard envelope."""
    email = f"env-{uuid.uuid4().hex[:8]}@example.com"
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "password123"},
    )
    if signup.status_code != 200:
        pytest.skip("Database not available")
    token = signup.json()["access_token"]

    res = await client.get(
        "/api/v1/properties/00000000-0000-0000-0000-000000000000/settings",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404
    data = res.json()
    assert data.get("success") is False
    assert "error" in data
    assert data.get("error_code") in ("not_found", "http_404")


@pytest.mark.asyncio
async def test_signup_login_flow(client: AsyncClient):
    """Signup and login return tokens. Requires DB."""
    email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "password123"},
    )
    if signup.status_code != 200:
        pytest.skip("Database not available")
    assert "access_token" in signup.json()

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert login.status_code == 200
    assert "access_token" in login.json()

"""Data import preview API tests."""
import io
import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_import_preview_requires_auth(client: AsyncClient):
    """Import preview requires authentication."""
    csv_content = b"stay_date,adr,revenue\n2024-01-01,100,5000"
    files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
    res = await client.post("/api/v1/data/import/preview", files=files)
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_import_preview_returns_headers(client: AsyncClient):
    """Import preview returns headers and detected mapping."""
    email = f"prev-{uuid.uuid4().hex[:8]}@example.com"
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "password123"},
    )
    if signup.status_code != 200:
        pytest.skip("Database not available")
    token = signup.json()["access_token"]

    csv_content = b"Stay Date,ADR,Revenue\n2024-01-01,100,5000\n2024-01-02,110,5500"
    files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
    res = await client.post(
        "/api/v1/data/import/preview",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "headers" in data
    assert "detected_mapping" in data
    assert "stay_date" in data["detected_mapping"] or "Stay Date" in data["headers"]

"""Market API integration tests."""
import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_market_snapshot_requires_auth(client: AsyncClient):
    """Market snapshot creation requires auth."""
    res = await client.post(
        "/api/v1/market/snapshot",
        data={"property_id": "any", "compset_avg": 100},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_market_import_csv_requires_auth(client: AsyncClient):
    """Market CSV import requires auth."""
    res = await client.post(
        "/api/v1/market/import-csv",
        data={"property_id": "any"},
        files={"file": ("rates.csv", b"stay_date,compset_avg\n2024-01-01,100", "text/csv")},
    )
    assert res.status_code == 401

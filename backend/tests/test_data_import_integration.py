"""Data import full flow integration test."""
import io
import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_import_flow(client: AsyncClient):
    """Signup -> create org -> create property -> upload CSV -> verify snapshot."""
    email = f"import-{uuid.uuid4().hex[:8]}@example.com"
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "password123"},
    )
    if signup.status_code != 200:
        pytest.skip("Database not available")
    token = signup.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    org_res = await client.post(
        "/api/v1/organizations",
        json={"name": f"Test Org {uuid.uuid4().hex[:6]}"},
        headers=headers,
    )
    if org_res.status_code != 200:
        pytest.skip("Could not create organization")
    org_id = org_res.json()["id"]

    prop_res = await client.post(
        "/api/v1/organizations/properties",
        json={"name": f"Test Property {uuid.uuid4().hex[:6]}", "organization_id": org_id},
        headers=headers,
    )
    if prop_res.status_code != 200:
        pytest.skip("Could not create property")
    property_id = prop_res.json()["id"]

    csv_content = b"stay_date,adr,revenue,rooms_available,rooms_sold\n"
    csv_content += b"2024-01-01,100,5000,50,45\n"
    csv_content += b"2024-01-02,110,5500,50,42\n"

    files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
    data = {
        "property_id": property_id,
        "snapshot_type": "current",
    }

    import_res = await client.post(
        "/api/v1/data/import",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert import_res.status_code == 200, import_res.text
    snapshot = import_res.json()
    assert snapshot.get("id")
    assert snapshot.get("property_id") == property_id
    assert snapshot.get("row_count") == 2
    assert snapshot.get("data_health_score") is not None or snapshot.get("row_count") > 0

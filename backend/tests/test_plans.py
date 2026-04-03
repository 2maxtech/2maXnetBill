import pytest

from app.core.config import settings

API = settings.API_V1_PREFIX


@pytest.mark.asyncio
async def test_create_plan(client, auth_headers):
    response = await client.post(
        f"{API}/plans/",
        json={
            "name": "Basic 10Mbps",
            "download_mbps": 10,
            "upload_mbps": 5,
            "monthly_price": "999.00",
            "description": "Basic plan",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Basic 10Mbps"
    assert data["download_mbps"] == 10
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_plans(client, auth_headers):
    await client.post(
        f"{API}/plans/",
        json={"name": "Plan A", "download_mbps": 10, "upload_mbps": 5, "monthly_price": "500.00"},
        headers=auth_headers,
    )
    await client.post(
        f"{API}/plans/",
        json={"name": "Plan B", "download_mbps": 20, "upload_mbps": 10, "monthly_price": "1000.00"},
        headers=auth_headers,
    )
    response = await client.get(f"{API}/plans/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_get_plan(client, auth_headers):
    create = await client.post(
        f"{API}/plans/",
        json={"name": "Test Plan", "download_mbps": 10, "upload_mbps": 5, "monthly_price": "500.00"},
        headers=auth_headers,
    )
    plan_id = create.json()["id"]

    response = await client.get(f"{API}/plans/{plan_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Test Plan"


@pytest.mark.asyncio
async def test_update_plan(client, auth_headers):
    create = await client.post(
        f"{API}/plans/",
        json={"name": "Old Name", "download_mbps": 10, "upload_mbps": 5, "monthly_price": "500.00"},
        headers=auth_headers,
    )
    plan_id = create.json()["id"]

    response = await client.put(
        f"{API}/plans/{plan_id}", json={"name": "New Name"}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_plan_soft(client, auth_headers):
    create = await client.post(
        f"{API}/plans/",
        json={"name": "To Delete", "download_mbps": 10, "upload_mbps": 5, "monthly_price": "500.00"},
        headers=auth_headers,
    )
    plan_id = create.json()["id"]

    response = await client.delete(f"{API}/plans/{plan_id}", headers=auth_headers)
    assert response.status_code == 204

    get_resp = await client.get(f"{API}/plans/{plan_id}", headers=auth_headers)
    assert get_resp.json()["is_active"] is False


@pytest.mark.asyncio
async def test_plan_not_found(client, auth_headers):
    response = await client.get(f"{API}/plans/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert response.status_code == 404

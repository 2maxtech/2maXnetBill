import pytest

from app.core.config import settings

API = settings.API_V1_PREFIX


@pytest.mark.asyncio
async def test_login_success(client, admin_user):
    response = await client.post(f"{API}/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client, admin_user):
    response = await client.post(f"{API}/auth/login", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    response = await client.post(f"{API}/auth/login", json={"username": "nobody", "password": "pass"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client, auth_headers):
    response = await client.get(f"{API}/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_get_me_no_token(client):
    response = await client.get(f"{API}/auth/me")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_refresh_token(client, admin_user):
    login = await client.post(f"{API}/auth/login", json={"username": "admin", "password": "admin123"})
    refresh_token = login.json()["refresh_token"]

    response = await client.post(f"{API}/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()

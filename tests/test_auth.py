"""
Tests for authentication router, code generation, and verification.
"""
import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport

from api.main import app
from api.routers.auth import auth_codes, _verify_attempts
from shared.config import get_settings

settings = get_settings()


@pytest.mark.asyncio
async def test_verify_code_invalid():
    """Verify that an unknown code returns 401, not 422 validation error."""
    _verify_attempts.clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/auth/verify-code", json={"code": "99999999"})
        assert resp.status_code == 401
        assert "Неверный или истёкший код" in resp.json().get("detail", "")


@pytest.mark.asyncio
async def test_verify_code_success():
    """Verify that a valid code logs in the user and returns JWT token."""
    _verify_attempts.clear()
    test_code = "12345678"
    auth_codes[test_code] = {
        "user_id": 999888,
        "user_data": {
            "id": 999888,
            "first_name": "TestAuth",
            "last_name": "User",
            "username": "testauthuser",
        },
        "expires": datetime.now(timezone.utc) + timedelta(minutes=5),
    }

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/api/auth/verify-code", json={"code": test_code})
            assert resp.status_code == 200
            data = resp.json()
            assert data["valid"] is True
            assert data["user"]["id"] == 999888
            assert data["token"] is not None
            # Code should be consumed
            assert test_code not in auth_codes
    finally:
        auth_codes.pop(test_code, None)

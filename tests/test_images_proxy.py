"""
Tests for image proxy endpoint and SSRF validation.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.routers.images import _is_safe_url, proxy_external_image
from fastapi import HTTPException


class TestSafeUrlValidation:
    """Tests for _is_safe_url SSRF guard."""

    def test_valid_https_url(self):
        assert _is_safe_url("https://i1.sndcdn.com/artworks-000123-large.jpg") is True
        assert _is_safe_url("https://i.scdn.co/image/ab67616d0000b2731234") is True
        assert _is_safe_url("http://example.com/cover.png") is True

    def test_disallow_non_http_schemes(self):
        assert _is_safe_url("file:///etc/passwd") is False
        assert _is_safe_url("ftp://ftp.example.com/image.jpg") is False
        assert _is_safe_url("javascript:alert(1)") is False
        assert _is_safe_url("data:image/png;base64,iVBORw0KGgo=") is False

    def test_disallow_localhost_and_zero(self):
        assert _is_safe_url("http://localhost/image.jpg") is False
        assert _is_safe_url("http://localhost:8000/image.jpg") is False
        assert _is_safe_url("http://0.0.0.0/image.jpg") is False

    def test_disallow_private_ip_ranges(self):
        assert _is_safe_url("http://127.0.0.1/cover.jpg") is False
        assert _is_safe_url("http://10.0.0.1/cover.jpg") is False
        assert _is_safe_url("http://192.168.1.1/cover.jpg") is False
        assert _is_safe_url("http://172.16.0.1/cover.jpg") is False
        assert _is_safe_url("http://169.254.169.254/latest/meta-data/") is False

    def test_disallow_empty_or_malformed(self):
        assert _is_safe_url("") is False
        assert _is_safe_url("not a url") is False
        assert _is_safe_url("http://") is False


@pytest.mark.asyncio
async def test_proxy_external_image_rejects_unsafe_url():
    with pytest.raises(HTTPException) as exc_info:
        await proxy_external_image("http://127.0.0.1/secret.jpg")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_proxy_external_image_success():
    """Test successful image proxying returns image data and Cache-Control."""
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.headers = {"Content-Type": "image/jpeg"}
    mock_resp.read = AsyncMock(return_value=b"\xff\xd8\xff\xe0fake_jpeg_content")

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_resp
    mock_cm.__aexit__.return_value = None

    mock_session = MagicMock()
    mock_session.get.return_value = mock_cm

    with patch("api.routers.images.get_http_session", AsyncMock(return_value=mock_session)):
        res = await proxy_external_image("https://i1.sndcdn.com/artworks-123-t500x500.jpg")
        assert res.status_code == 200
        assert res.media_type == "image/jpeg"
        assert res.body == b"\xff\xd8\xff\xe0fake_jpeg_content"
        assert "max-age=604800" in res.headers["Cache-Control"]

"""
Tests for API schemas (v2)
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from api.schemas.common import TelegramUser
from api.schemas.tracks import TrackResponse, TrackUpdate
from api.schemas.player import StreamUrlResponse


class TestTelegramUser:
    """Tests for TelegramUser schema"""
    
    def test_valid_user(self):
        user = TelegramUser(
            id=123456789,
            first_name="Test",
            username="testuser"
        )
        assert user.id == 123456789
        assert user.first_name == "Test"
        assert user.username == "testuser"
    
    def test_minimal_user(self):
        user = TelegramUser(id=1, first_name="A")
        assert user.id == 1
        assert user.last_name is None
        assert user.username is None
    
    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            TelegramUser(first_name="Test")  # Missing id


class TestTrackSchemas:
    """Tests for Track-related schemas"""
    
    def test_track_update_partial(self):
        update = TrackUpdate(title="New Title")
        assert update.title == "New Title"
        assert update.artist is None
    
    def test_track_response(self):
        response = TrackResponse(
            id=1,
            telegram_file_id="abc123",
            title="Test",
            artist="Artist",
            added_at=datetime.now()
        )
        assert response.id == 1
        assert response.is_liked == False
        assert response.play_count == 0


from api.schemas.playlists import PlaylistResponse


class TestStreamUrlResponse:
    """Tests for StreamUrlResponse schema"""
    
    def test_valid_response(self):
        response = StreamUrlResponse(
            url="/api/player/audio/abc123",
            expires_at=1700000000,
            track_id=42
        )
        assert response.track_id == 42
        assert "/api/player/audio/" in response.url


class TestPlaylistSchemas:
    """Tests for Playlist schemas"""

    def test_playlist_response_with_updated_at(self):
        now = datetime.now()
        pl = PlaylistResponse(
            id=1,
            name="Test Playlist",
            created_at=now,
            updated_at=now,
        )
        assert pl.id == 1
        assert pl.name == "Test Playlist"
        assert pl.created_at == now
        assert pl.updated_at == now

    def test_playlist_response_default_updated_at(self):
        now = datetime.now()
        pl = PlaylistResponse(
            id=2,
            name="Another Playlist",
            created_at=now,
        )
        assert pl.id == 2
        assert pl.updated_at is None

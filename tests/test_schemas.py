"""
Tests for API schemas
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from api.schemas import (
    TelegramUser,
    TrackBase,
    TrackUpdate,
    TrackResponse,
    PlaylistBase,
    PlaylistCreate,
    StreamUrlResponse,
)


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
    
    def test_track_base(self):
        track = TrackBase(
            title="Song",
            artist="Artist",
            album="Album"
        )
        assert track.title == "Song"
        assert track.genre is None
    
    def test_track_update_partial(self):
        update = TrackUpdate(title="New Title")
        assert update.title == "New Title"
        assert update.artist is None
        assert update.is_public is None
    
    def test_track_response(self):
        response = TrackResponse(
            id=1,
            file_id="abc123",
            title="Test",
            artist="Artist",
            created_at=datetime.now()
        )
        assert response.id == 1
        assert response.is_liked == False
        assert response.play_count == 0


class TestPlaylistSchemas:
    """Tests for Playlist-related schemas"""
    
    def test_playlist_base(self):
        playlist = PlaylistBase(name="My Playlist")
        assert playlist.name == "My Playlist"
        assert playlist.description is None
    
    def test_playlist_create(self):
        playlist = PlaylistCreate(
            name="New Playlist",
            description="Test description"
        )
        assert playlist.name == "New Playlist"
    
    def test_playlist_name_required(self):
        with pytest.raises(ValidationError):
            PlaylistBase(description="No name")


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

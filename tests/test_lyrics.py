"""
Tests for Lyrics functionality
"""
import pytest
from bot.services.lyrics.lrclib import lrclib_client
from shared.models import TrackLyrics
from api.schemas.tracks import TrackLyricsResponse, TrackLyricsUpdate, TrackLyricsOffsetUpdate


def test_lrclib_format_result():
    data = {
        "id": 123,
        "trackName": "Bohemian Rhapsody",
        "artistName": "Queen",
        "syncedLyrics": "[00:00.15] Is this the real life?\n[00:07.13] Caught in a landslide",
        "plainLyrics": "Is this the real life?\nCaught in a landslide",
        "instrumental": False
    }
    res = lrclib_client._format_result(data)
    assert res["plain_lyrics"] == "Is this the real life?\nCaught in a landslide"
    assert res["is_synced"] is True
    assert res["is_instrumental"] is False
    assert res["source"] == "lrclib"


def test_lrclib_format_instrumental():
    data = {
        "id": 456,
        "trackName": "Intro",
        "artistName": "The xx",
        "syncedLyrics": None,
        "plainLyrics": None,
        "instrumental": True
    }
    res = lrclib_client._format_result(data)
    assert res["is_instrumental"] is True
    assert res["is_synced"] is False
    assert res["plain_lyrics"] is None


def test_lyrics_schemas():
    resp = TrackLyricsResponse(
        track_id=1,
        plain_lyrics="Hello world",
        synced_lyrics="[00:01.00] Hello world",
        is_synced=True,
        is_instrumental=False,
        source="lrclib",
        offset_ms=500
    )
    assert resp.track_id == 1
    assert resp.offset_ms == 500
    assert resp.is_synced is True

    update = TrackLyricsUpdate(
        plain_lyrics="Updated",
        offset_ms=-200
    )
    assert update.plain_lyrics == "Updated"
    assert update.offset_ms == -200

    offset_update = TrackLyricsOffsetUpdate(offset_ms=300)
    assert offset_update.offset_ms == 300

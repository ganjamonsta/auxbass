"""
Tests for External Music Ingestion Framework (SoundCloud, Providers, Registry, Jobs)
"""
import pytest
import asyncio
from bot.services.ingestion.base import EntityType, SourceEntity, TrackMetadata
from bot.services.ingestion.registry import ProviderRegistry, provider_registry
from bot.services.ingestion.job_manager import IngestionJobManager, JobStatus
from bot.services.ingestion.providers.soundcloud import (
    SoundCloudProvider,
    _parse_artist_and_title,
    _improve_sc_thumbnail,
)


def test_soundcloud_url_matching():
    sc = SoundCloudProvider()
    assert sc.can_handle("https://soundcloud.com/artist/track-title")
    assert sc.can_handle("https://m.soundcloud.com/artist/track-title")
    assert sc.can_handle("https://on.soundcloud.com/xyz123")
    assert sc.can_handle("https://soundcloud.com/artist/sets/my-playlist")
    assert not sc.can_handle("https://youtube.com/watch?v=12345")
    assert not sc.can_handle("https://open.spotify.com/track/12345")


def test_soundcloud_title_and_artist_parsing():
    # Format "Artist - Title"
    artist, title = _parse_artist_and_title("Daft Punk - One More Time", "Daft Punk Official")
    assert artist == "Daft Punk"
    assert title == "One More Time"

    # Format without separator: fallback to uploader
    artist, title = _parse_artist_and_title("Just A Track", "Skrillex")
    assert artist == "Skrillex"
    assert title == "Just A Track"


def test_soundcloud_thumbnail_upgrade():
    original = "https://i1.sndcdn.com/artworks-000123-large.jpg"
    upgraded = _improve_sc_thumbnail(original)
    assert upgraded == "https://i1.sndcdn.com/artworks-000123-t500x500.jpg"
    assert _improve_sc_thumbnail(None) is None


def test_provider_registry():
    registry = ProviderRegistry()
    assert "soundcloud" in registry.list_providers()
    
    provider = registry.find_provider("https://soundcloud.com/forss/flickermood")
    assert provider is not None
    assert provider.name == "soundcloud"

    unknown = registry.find_provider("https://unknown-music.org/track/1")
    assert unknown is None


@pytest.mark.asyncio
async def test_job_manager_flow():
    mgr = IngestionJobManager()
    job = await mgr.create_job(
        user_id=12345,
        url="https://soundcloud.com/test/track",
        provider_name="soundcloud",
        entity_type="track",
        title="Test Track",
        total_tracks=1,
        author="Test Artist",
    )

    assert job.id is not None
    assert job.user_id == 12345
    assert job.status == JobStatus.PENDING
    assert job.progress_percent == 0

    # Retrieve
    retrieved = mgr.get_job(job.id)
    assert retrieved == job

    # User jobs
    user_jobs = mgr.get_user_jobs(12345)
    assert len(user_jobs) == 1
    assert user_jobs[0].id == job.id

    # Progress calculation
    job.total_tracks = 10
    job.processed_tracks = 5
    assert job.progress_percent == 50

    job.processed_tracks = 10
    job.status = JobStatus.COMPLETED
    assert job.progress_percent == 100

    # Cancellation
    mgr.cancel_job(job.id)
    assert job.status == JobStatus.CANCELLED


@pytest.mark.asyncio
async def test_soundcloud_search_mock(monkeypatch):
    sc = SoundCloudProvider()
    
    async def mock_to_thread(func):
        return {
            "entries": [
                {
                    "title": "Test Artist - Cool Song",
                    "uploader": "Test Artist",
                    "webpage_url": "https://soundcloud.com/test/cool-song",
                    "duration": 180,
                    "thumbnail": "https://i1.sndcdn.com/artworks-0001-large.jpg",
                    "id": "112233",
                }
            ]
        }
    
    monkeypatch.setattr(asyncio, "to_thread", mock_to_thread)
    results = await sc.search("Cool Song", limit=1)
    assert len(results) == 1
    assert results[0].artist == "Test Artist"
    assert results[0].title == "Cool Song"
    assert results[0].duration == 180
    assert "t500x500" in results[0].cover_url


@pytest.mark.asyncio
async def test_job_manager_selective_import():
    mgr = IngestionJobManager()
    selected = ["https://soundcloud.com/test/track-1", "https://soundcloud.com/test/track-3"]
    job = await mgr.create_job(
        user_id=999,
        url="https://soundcloud.com/test/sets/playlist",
        provider_name="soundcloud",
        entity_type="playlist",
        title="Test Playlist",
        total_tracks=len(selected),
        selected_urls=selected,
    )

    assert job.selected_urls == selected
    assert job.total_tracks == 2
    d = job.to_dict()
    assert d["selected_urls"] == selected


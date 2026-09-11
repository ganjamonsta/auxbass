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


@pytest.mark.asyncio
async def test_soundcloud_search_thumbnails_list_mock(monkeypatch):
    sc = SoundCloudProvider()

    async def mock_to_thread(func):
        return {
            "entries": [
                {
                    "title": "andy warhol",
                    "uploader": "Kai Angel & 9mice",
                    "webpage_url": "https://soundcloud.com/test/andy-warhol",
                    "duration": 173,
                    "thumbnail": None,
                    "thumbnails": [
                        {"id": "mini", "url": "https://i1.sndcdn.com/artworks-123-mini.jpg"},
                        {"id": "t500x500", "url": "https://i1.sndcdn.com/artworks-123-t500x500.jpg"},
                    ],
                    "id": "999888",
                }
            ]
        }

    monkeypatch.setattr(asyncio, "to_thread", mock_to_thread)
    results = await sc.search("andy warhol", limit=1)
    assert len(results) == 1
    assert results[0].cover_url == "https://i1.sndcdn.com/artworks-123-t500x500.jpg"


@pytest.mark.asyncio
async def test_soundcloud_user_profile_and_likes_mock(monkeypatch):
    sc = SoundCloudProvider()
    sc._cached_client_id = "test_client_id"

    # Mock resolve_user_profile HTTP call
    class MockResponse:
        def __init__(self, data, status=200):
            self._data = data
            self.status = status

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def json(self):
            return self._data

        async def text(self):
            return str(self._data)

    profile_payload = {
        "id": 123456,
        "permalink": "cool_artist",
        "username": "Cool Artist",
        "avatar_url": "https://i1.sndcdn.com/avatars-000-large.jpg",
        "permalink_url": "https://soundcloud.com/cool_artist",
        "likes_count": 42,
        "track_count": 10,
    }

    likes_payload = {
        "collection": [
            {
                "created_at": "2026-01-01T00:00:00Z",
                "track": {
                    "id": 98765,
                    "title": "Banger Track",
                    "user": {"username": "Another Producer", "permalink": "producer"},
                    "permalink_url": "https://soundcloud.com/producer/banger-track",
                    "duration": 180000,
                    "artwork_url": "https://i1.sndcdn.com/artworks-999-large.jpg",
                },
            }
        ],
        "next_href": "https://api-v2.soundcloud.com/users/123456/likes?offset=2",
    }

    class MockSession:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        def get(self, url, **kwargs):
            if "/resolve" in str(url):
                return MockResponse(profile_payload)
            if "/likes" in str(url):
                return MockResponse(likes_payload)
            return MockResponse({}, status=404)

    import aiohttp
    monkeypatch.setattr(aiohttp, "ClientSession", MockSession)

    # 1. Test profile resolution
    prof = await sc.resolve_user_profile("cool_artist")
    assert prof["external_id"] == "123456"
    assert prof["username"] == "cool_artist"
    assert prof["display_name"] == "Cool Artist"
    assert prof["likes_count"] == 42
    assert "t500x500" in prof["avatar_url"]

    # 2. Test user likes fetching
    likes, next_cursor = await sc.fetch_user_likes("123456", limit=10)
    assert len(likes) == 1
    assert likes[0].title == "Banger Track"
    assert likes[0].artist == "Another Producer"
    assert likes[0].duration == 180
    assert "t500x500" in likes[0].cover_url
    assert next_cursor == "https://api-v2.soundcloud.com/users/123456/likes?offset=2"


@pytest.mark.asyncio
async def test_soundcloud_drm_protection_handling(monkeypatch):
    sc = SoundCloudProvider()
    meta = TrackMetadata(
        provider_name="soundcloud",
        url="https://soundcloud.com/pendulum/fasten-your-seatbelt-ft-the",
        title="Fasten Your Seatbelt",
        artist="Pendulum",
    )

    class MockYDL:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def download(self, urls):
            import yt_dlp
            raise yt_dlp.utils.DownloadError("\x1b[0;31mERROR:\x1b[0m [soundcloud] 1236088255: This video is DRM protected")

    import yt_dlp
    monkeypatch.setattr(yt_dlp, "YoutubeDL", MockYDL)

    with pytest.raises(ValueError) as exc_info:
        await sc.download_track(meta, "/tmp/fake_dir")

    assert "защищён DRM" in str(exc_info.value)
    assert "\x1b[" not in str(exc_info.value)


def test_quick_import_request_and_search_response_schemas():
    from api.routers.ingestion import QuickImportRequest, SearchItemResponse

    # Defaults to add_to_library = False
    req = QuickImportRequest(url="https://soundcloud.com/artist/track")
    assert req.add_to_library is False

    req_add = QuickImportRequest(url="https://soundcloud.com/artist/track", add_to_library=True)
    assert req_add.add_to_library is True

    search_item = SearchItemResponse(
        provider="soundcloud",
        url="https://soundcloud.com/artist/track",
        title="Track",
        artist="Artist",
        in_library=True,
        in_channel=False,
        already_in_tg=True,
    )
    assert search_item.in_library is True
    assert search_item.already_in_tg is True





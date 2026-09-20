import pytest
from shared.matching import is_bogus_album_name, sanitize_album_name
from bot.services.ingestion.base import EntityType
from bot.services.ingestion.providers.spotify import SpotifyProvider
from bot.services.ingestion.providers.soundcloud import SoundCloudProvider
from bot.services.ingestion.providers.youtube import YouTubeMusicProvider


def test_is_bogus_album_name():
    # Bogus / pseudo-album patterns
    assert is_bogus_album_name("meth (Likes)") is True
    assert is_bogus_album_name("user (Likes)") is True
    assert is_bogus_album_name("Likes") is True
    assert is_bogus_album_name("Liked Songs") is True
    assert is_bogus_album_name("SoundCloud Likes") is True
    assert is_bogus_album_name("Spotify Likes") is True
    assert is_bogus_album_name("YouTube Likes") is True
    assert is_bogus_album_name("Любимые треки") is True
    assert is_bogus_album_name("Понравившиеся") is True
    assert is_bogus_album_name("Likes (user)") is True

    # Real legitimate albums with "like" in title must NOT be bogus
    assert is_bogus_album_name("Act Like You Know") is False
    assert is_bogus_album_name("Nothing Like Uuu - Single") is False
    assert is_bogus_album_name("SEEMS LIKE IN THE SYSTEM") is False
    assert is_bogus_album_name("Play Em Like Atari") is False
    assert is_bogus_album_name("Like Me") is False
    assert is_bogus_album_name("Like a Boss EP") is False
    assert is_bogus_album_name("Would You Like A Sample") is False
    assert is_bogus_album_name("Starboy") is False
    assert is_bogus_album_name(None) is False
    assert is_bogus_album_name("") is False


def test_sanitize_album_name():
    assert sanitize_album_name("meth (Likes)") is None
    assert sanitize_album_name("SoundCloud Likes") is None
    assert sanitize_album_name("Act Like You Know") == "Act Like You Know"
    assert sanitize_album_name("Starboy") == "Starboy"
    assert sanitize_album_name(None) is None


def test_provider_url_matching():
    sp = SpotifyProvider()
    assert sp.can_handle("https://open.spotify.com/album/4vS9W9N9vS9") is True
    assert sp.can_handle("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M") is True
    assert sp.can_handle("https://open.spotify.com/track/11dFghVXANMlKmJXsNCbNl") is True

    sc = SoundCloudProvider()
    assert sc.can_handle("https://soundcloud.com/user/sets/my-playlist") is True
    assert sc.can_handle("https://on.soundcloud.com/abc123") is True

    yt = YouTubeMusicProvider()
    assert yt.can_handle("https://music.youtube.com/playlist?list=OLAK5uy_k123") is True
    assert yt.can_handle("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True
    assert yt.can_handle("https://youtu.be/dQw4w9WgXcQ") is True

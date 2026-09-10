"""
TG Player - Ingestion Base Models & Abstract Provider Interface
Scalable foundation for external audio sources (SoundCloud, Spotify, YouTube Music, etc.)
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class EntityType(str, Enum):
    TRACK = "track"
    PLAYLIST = "playlist"
    ALBUM = "album"
    ARTIST = "artist"


@dataclass
class SourceEntity:
    """Represents a resolved external URL before or during import."""
    provider_name: str
    entity_type: EntityType
    url: str
    title: str
    author: Optional[str] = None
    cover_url: Optional[str] = None
    track_count: int = 1
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class TrackMetadata:
    """Metadata for a single track from an external provider."""
    provider_name: str
    url: str
    title: str
    artist: str
    album: Optional[str] = None
    duration: Optional[int] = None
    cover_url: Optional[str] = None
    track_number: Optional[int] = None
    isrc: Optional[str] = None
    external_id: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DownloadedAudio:
    """Result of downloading an audio stream and its artwork to local disk."""
    audio_path: str
    cover_path: Optional[str] = None
    metadata: Optional[TrackMetadata] = None
    file_size: int = 0
    mime_type: str = "audio/mpeg"


class BaseMusicProvider(ABC):
    """Abstract interface for external music providers."""
    name: str = "base"

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Return True if this provider can handle the given URL."""
        pass

    @abstractmethod
    async def resolve_entity(self, url: str) -> SourceEntity:
        """
        Quickly inspect URL and return high-level entity metadata (title, count, cover)
        without downloading audio streams.
        """
        pass

    @abstractmethod
    async def fetch_tracklist(self, entity: SourceEntity) -> List[TrackMetadata]:
        """Fetch list of all tracks in the entity (1 for track, N for playlist/album)."""
        pass

    @abstractmethod
    async def download_track(self, track_meta: TrackMetadata, temp_dir: str) -> DownloadedAudio:
        """Download track audio and artwork into the specified directory."""
        pass

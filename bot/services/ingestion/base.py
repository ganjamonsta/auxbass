"""
TG Player - Ingestion Base Models & Abstract Provider Interface
Scalable foundation for external audio sources (SoundCloud, Spotify, YouTube Music, etc.)
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Callable


class EntityType(str, Enum):
    TRACK = "track"
    PLAYLIST = "playlist"
    ALBUM = "album"
    ARTIST = "artist"
    TRACKS = "tracks"


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


def calculate_preview_range(total_duration: Optional[int], chunk_seconds: int = 30) -> tuple[int, int]:
    """
    Calculate start and end seconds for a fast audio preview chunk.
    Skips long/empty intros (ambient, beat-only) to land on the vocal/chorus/drop.
    """
    if not total_duration or total_duration <= chunk_seconds:
        return (0, chunk_seconds)
    
    # For very short tracks (<= 60s), start at 10s
    if total_duration <= 60:
        start = max(0, min(10, total_duration - chunk_seconds))
        return (start, start + chunk_seconds)
    
    # For 60-120s tracks: intro is usually 15-20s -> start at 20s
    if total_duration <= 120:
        start = 20
        return (start, start + chunk_seconds)
    
    # For normal tracks (> 120s):
    # Sweet spot is ~25% into the track (where first verse/chorus kicks in)
    start = int(total_duration * 0.25)
    # Bound start between 25s and 60s
    start = max(25, min(60, start))
    
    # Guard against exceeding total duration
    if start + chunk_seconds > total_duration:
        start = max(0, total_duration - chunk_seconds)
        
    return (start, start + chunk_seconds)


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
    async def download_track(
        self,
        track_meta: TrackMetadata,
        temp_dir: str,
        progress_hook: Optional[Callable[[int], None]] = None,
        chunk_only: bool = False,
        chunk_duration: int = 30,
        chunk_start: Optional[int] = None,
    ) -> DownloadedAudio:
        """Download track audio and artwork into the specified directory."""
        pass

    async def search(self, query: str, limit: int = 15) -> List[TrackMetadata]:
        """Search tracks by keyword on the external provider (if supported)."""
        return []


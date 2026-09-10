"""
TG Player - Ingestion Services Package
"""
from .base import BaseMusicProvider, SourceEntity, TrackMetadata, DownloadedAudio, EntityType
from .registry import provider_registry, ProviderRegistry
from .job_manager import job_manager, IngestionJob, JobStatus, IngestionJobManager
from .pipeline import IngestionPipeline

__all__ = [
    "BaseMusicProvider",
    "SourceEntity",
    "TrackMetadata",
    "DownloadedAudio",
    "EntityType",
    "provider_registry",
    "ProviderRegistry",
    "job_manager",
    "IngestionJob",
    "JobStatus",
    "IngestionJobManager",
    "IngestionPipeline",
]

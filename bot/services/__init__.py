"""
TG Player Bot - Services
"""
from .metadata import metadata_service
from .enrichment import enrichment_worker

# New service modules
from .tracks import track_service, TrackService
from .channels import (
    channel_service,
    ChannelService,
    init_channel_service,
    start_channel_service,
    stop_channel_service,
)
from .albums import album_service, AlbumService
from .deduplication import deduplication_service, DeduplicationService

__all__ = [
    'metadata_service',
    'enrichment_worker',
    'track_service',
    'TrackService', 
    'channel_service',
    'ChannelService',
    'init_channel_service',
    'start_channel_service',
    'stop_channel_service',
    'album_service',
    'AlbumService',
    'deduplication_service',
    'DeduplicationService',
]

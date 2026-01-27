"""
TG Player - Bot Services Module

Central service layer for all bot operations.

Services:
- tracks: Unified track management (save, update, delete, search)
- enrichment: Metadata enrichment from Deezer/Last.fm
- albums: Album assembly and grouping
- channels: User channel backup management
"""
from .tracks import track_service, TrackService, SaveTrackResult, TrackSearchResult
from .albums import album_service, AlbumService, AlbumCandidate
from .enrichment import enrichment_worker, enrichment_processor, EnrichmentResult
from .channels import channel_service, ChannelService

__all__ = [
    # Track service
    "track_service",
    "TrackService",
    "SaveTrackResult",
    "TrackSearchResult",
    
    # Album service
    "album_service",
    "AlbumService",
    "AlbumCandidate",
    
    # Enrichment
    "enrichment_worker",
    "enrichment_processor",
    "EnrichmentResult",
    
    # Channels
    "channel_service",
    "ChannelService",
]

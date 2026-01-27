"""
TG Player - Track Service Module

Provides unified track management with automatic enrichment and album assignment.
"""
from .service import TrackService, SaveTrackResult, TrackSearchResult, track_service

__all__ = [
    "TrackService",
    "SaveTrackResult",
    "TrackSearchResult",
    "track_service",
]

"""
TG Player - Enrichment Service Module

Provides track metadata enrichment from external sources (Deezer, Last.fm).
"""
from .processor import EnrichmentProcessor, EnrichmentResult, enrichment_processor
from .worker import EnrichmentWorker, enrichment_worker
from .deezer import DeezerClient, deezer_client
from .lastfm import LastFmClient, lastfm_client

__all__ = [
    # Main classes
    "EnrichmentProcessor",
    "EnrichmentResult", 
    "EnrichmentWorker",
    "DeezerClient",
    "LastFmClient",
    
    # Global instances
    "enrichment_processor",
    "enrichment_worker",
    "deezer_client",
    "lastfm_client",
]

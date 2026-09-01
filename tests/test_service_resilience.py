"""
Unit tests for service resilience and memory safety
"""
import time
import pytest
from bot.services.enrichment.worker import EnrichmentWorker
from bot.services.channels.service import ChannelService
from api.main import RateLimitMiddleware


def test_rate_limit_cleanup_stale_ips():
    """Verify that RateLimitMiddleware purges expired IP entries and prevents memory leaks"""
    middleware = RateLimitMiddleware(app=None, requests_per_minute=10)
    
    now = time.time()
    # Add active IP (recent request)
    middleware.requests["1.1.1.1"] = [now - 10, now - 5]
    
    # Add stale IP (request was 70 seconds ago)
    middleware.requests["2.2.2.2"] = [now - 70]
    
    # Add empty IP list
    middleware.requests["3.3.3.3"] = []
    
    # Run cleanup
    middleware._cleanup_stale_ips(now)
    
    # Assert stale and empty IPs were purged
    assert "1.1.1.1" in middleware.requests
    assert "2.2.2.2" not in middleware.requests
    assert "3.3.3.3" not in middleware.requests
    assert len(middleware.requests) == 1


def test_enrichment_worker_event_notification():
    """Verify that EnrichmentWorker event is triggered by notify_new_track"""
    worker = EnrichmentWorker()
    event = worker._get_event()
    assert not event.is_set()
    
    worker.notify_new_track()
    assert event.is_set()
    
    event.clear()
    assert not event.is_set()


def test_channel_service_queue_event():
    """Verify that ChannelService signals queue event on track enqueue"""
    service = ChannelService()
    event = service._get_queue_event()
    assert not event.is_set()
    
    service.queue_track_for_forward(user_id=123, track_id=456)
    assert event.is_set()
    assert service.get_queue_size() == 1

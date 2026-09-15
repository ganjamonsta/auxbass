"""
TG Player - Ingestion Provider Registry
Dispatches URLs to matching providers (SoundCloud, Spotify, etc.)
"""
import logging
from typing import Dict, List, Optional

from .base import BaseMusicProvider
from .providers.soundcloud import SoundCloudProvider
from .providers.spotify import SpotifyProvider
from .providers.youtube import YouTubeMusicProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Registry holding all supported music source providers."""

    def __init__(self):
        self._providers: Dict[str, BaseMusicProvider] = {}
        self._register_default_providers()

    def _register_default_providers(self):
        """Register built-in providers."""
        self.register(SoundCloudProvider())
        self.register(SpotifyProvider())
        self.register(YouTubeMusicProvider())

    def register(self, provider: BaseMusicProvider):
        """Register a provider instance."""
        self._providers[provider.name] = provider
        logger.info(f"Registered music provider: {provider.name}")

    def get_provider(self, name: str) -> Optional[BaseMusicProvider]:
        """Get provider by its identifier name."""
        return self._providers.get(name)

    def find_provider(self, url: str) -> Optional[BaseMusicProvider]:
        """Find the appropriate provider that can handle the given URL."""
        clean_url = url.strip()
        for provider in self._providers.values():
            if provider.can_handle(clean_url):
                return provider
        return None

    def list_providers(self) -> List[str]:
        """List registered provider names."""
        return list(self._providers.keys())


# Global singleton instance
provider_registry = ProviderRegistry()

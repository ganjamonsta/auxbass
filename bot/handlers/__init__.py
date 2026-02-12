"""Bot handlers"""
from . import menu, audio, download, deduplication, channel_pins

# menu.py replaces the old commands.py + callbacks.py
# It provides the unified hierarchical menu with FSM and all callback handlers.
__all__ = ["menu", "audio", "download", "deduplication", "channel_pins"]

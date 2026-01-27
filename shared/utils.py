"""
TG Player - Shared Utilities

This module re-exports functions from matching.py for backward compatibility
and provides formatting utilities.
"""
import re
from typing import Optional, List

# Re-export from matching module for backward compatibility
from .matching import (
    # Normalization
    normalize_unicode,
    normalize_artist,
    normalize_title,
    normalize_album,
    normalize_genre,
    clean_for_search,
    remove_parenthetical,
    remove_featuring,
    
    # Matching
    fuzzy_match_title,
    fuzzy_match_artist,
    artists_match,
    titles_match,
    jaccard_similarity,
    
    # Sanitization
    sanitize_input,
    sanitize_search_query,
    
    # Hashtags
    generate_hashtags,
    format_hashtags,
    
    # Constants
    ARTIST_MATCH_THRESHOLD,
    TITLE_MATCH_THRESHOLD,
    ALBUM_MATCH_THRESHOLD,
    GENRE_MAPPINGS,
)


# ============== Formatting ==============

def format_duration(seconds: Optional[int]) -> str:
    """Format duration in seconds to MM:SS or HH:MM:SS"""
    if not seconds:
        return "0:00"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_duration_long(seconds: Optional[int]) -> str:
    """Format duration in human-readable form (e.g., '1 ч 23 мин')"""
    if not seconds:
        return "0 мин"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours} ч {minutes} мин"
    return f"{minutes} мин"


def format_file_size(bytes_size: Optional[int]) -> str:
    """Format file size in human-readable form"""
    if not bytes_size:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    
    return f"{bytes_size:.1f} TB"


def format_track_info(
    title: Optional[str] = None,
    artist: Optional[str] = None,
    duration: Optional[int] = None,
    include_duration: bool = True
) -> str:
    """
    Format track info for display.
    
    Examples:
        "Track Name - Artist (3:45)"
        "Track Name - Unknown Artist"
    """
    parts = []
    
    title_str = title or "Без названия"
    artist_str = artist or "Неизвестный исполнитель"
    
    parts.append(f"{title_str} — {artist_str}")
    
    if include_duration and duration:
        parts.append(f"({format_duration(duration)})")
    
    return " ".join(parts)


# ============== Artist Splitting ==============

# Regex pattern to split multiple artists
ARTIST_SPLIT_PATTERN = re.compile(
    r'\s*[,&+]\s*'  # Symbols: comma, ampersand, plus
    r'|'
    r'\s+(?:feat\.?|ft\.?|featuring)\s+'  # Features
    r'|'
    r'\s+(?:x|vs\.?)\s+'  # Collaborations
    r'|'
    r'\s+(?:and|with)\s+'  # Conjunctions
    r'|'
    r'\s+(?:prod\.?|produced\s+by)\s+'  # Producers
    , flags=re.IGNORECASE
)


def split_artists(artist_string: str) -> List[str]:
    """
    Split a string containing multiple artists into a list.
    Handles: commas, ampersands, feat., ft., x, vs., and, with, prod.
    
    Example: "Artist1, Artist2 & Artist3 feat. Artist4" 
             -> ["Artist1", "Artist2", "Artist3", "Artist4"]
    """
    if not artist_string:
        return []
    
    artists = ARTIST_SPLIT_PATTERN.split(artist_string)
    return [a.strip() for a in artists if a.strip()]


def get_primary_artist(artist_string: str) -> str:
    """
    Get the primary (first) artist from a collaboration string.
    
    Example: "Drake, Future" -> "Drake"
    """
    artists = split_artists(artist_string)
    return artists[0] if artists else artist_string or ""


# ============== Telegram Helpers ==============

def escape_html(text: str) -> str:
    """Escape HTML special characters for Telegram messages."""
    if not text:
        return ""
    return (
        text
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
    )


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length, adding suffix if truncated."""
    if not text or len(text) <= max_length:
        return text or ""
    
    return text[:max_length - len(suffix)] + suffix

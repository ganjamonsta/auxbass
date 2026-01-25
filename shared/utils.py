"""
TG Player - Shared Utilities
Common functions used across API and Bot
"""
import re
import unicodedata
from typing import Optional


# ============== Input Sanitization ==============

def sanitize_input(value: str, max_length: int = 200) -> str:
    """
    Sanitize user input to prevent SQL injection.
    Use for search queries, filters, and any user-provided strings.
    """
    if not value:
        return ""
    # Escape SQL wildcards
    value = value.replace('%', r'\%').replace('_', r'\_')
    return value[:max_length].strip()


def sanitize_search_query(query: str, max_length: int = 100) -> str:
    """
    Sanitize search input - more aggressive for search queries.
    Removes SQL special characters and limits length.
    """
    if not query:
        return ""
    # Remove SQL special characters
    query = re.sub(r'[;\'"\\%_]', '', query)
    return query[:max_length].strip()


# ============== Text Normalization ==============

def normalize_artist(artist: str) -> str:
    """
    Normalize artist name for comparison/grouping.
    - Takes first artist from collaborations
    - Removes feat./prod. suffixes
    - Normalizes case and special chars
    
    Use for: matching, deduplication, grouping
    """
    if not artist:
        return ""
    
    artist = artist.lower()
    
    # Remove content in parentheses
    artist = re.sub(r'\s*[\(\[].*?[\)\]]', '', artist)
    
    # Remove feat., ft., prod., etc. and everything after
    artist = re.sub(
        r'\s*(feat\.?|ft\.?|featuring|vs\.?|prod\.?|produced\s+by)\s+.*',
        '', artist, flags=re.IGNORECASE
    )
    
    # Take first artist from list (separators: comma, ampersand, plus, x, and, with)
    artist = re.split(
        r'\s*[,&+]\s*|\s+(?:x|and|with)\s+',
        artist, flags=re.IGNORECASE
    )[0]
    
    # Replace $ with s (A$AP -> ASAP), remove special chars
    artist = artist.replace('$', 's')
    artist = re.sub(r'[^\w\s]', '', artist)
    
    # Normalize whitespace
    artist = ' '.join(artist.split())
    
    return artist.strip()


def normalize_title(title: str) -> str:
    """
    Normalize track title for comparison.
    - Removes parenthetical content (feat., remix, etc.)
    - Normalizes unicode and case
    - Removes special characters
    
    Use for: matching tracks, deduplication
    """
    if not title:
        return ""
    
    # Normalize unicode (curly apostrophes -> straight)
    title = unicodedata.normalize('NFKD', title)
    title = title.lower()
    
    # Remove content in parentheses/brackets
    title = re.sub(r'\s*\([^)]*\)', '', title)
    title = re.sub(r'\s*\[[^\]]*\]', '', title)
    
    # Remove "feat." / "ft." and everything after
    title = re.sub(r'\s*(feat\.?|ft\.?)\s+.*$', '', title, flags=re.IGNORECASE)
    
    # Normalize apostrophes and remove them
    title = title.replace("'", "'").replace("'", "'").replace("`", "'")
    title = title.replace("'", "")
    
    # Remove special characters, keep letters/numbers/spaces
    title = re.sub(r"[^\w\s]", '', title)
    
    # Normalize spaces
    title = ' '.join(title.split())
    
    return title.strip()


def clean_search_string(s: str) -> str:
    """
    Clean string for external API search queries.
    Removes parenthetical content and feature credits.
    """
    if not s:
        return ""
    # Remove content in parentheses/brackets
    s = re.sub(r'\s*[\(\[].*?[\)\]]', '', s)
    # Remove feat., ft., prod., etc. and everything after
    s = re.sub(
        r'\s*(feat\.?|ft\.?|featuring|vs\.?|prod\.?|produced\s+by)\s+.*',
        '', s, flags=re.IGNORECASE
    )
    return s.strip()


def fuzzy_match_strings(s1: str, s2: str, threshold: float = 0.6) -> bool:
    """
    Check if two strings match using word-based Jaccard similarity.
    
    Args:
        s1: First string (will be normalized)
        s2: Second string (will be normalized)
        threshold: Minimum similarity (0.0 to 1.0)
    
    Returns:
        True if strings match above threshold
    """
    norm1 = normalize_title(s1)
    norm2 = normalize_title(s2)
    
    if not norm1 or not norm2:
        return False
    
    # Exact match
    if norm1 == norm2:
        return True
    
    # One contains the other
    if norm1 in norm2 or norm2 in norm1:
        return True
    
    # Jaccard similarity on words
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if not words1 or not words2:
        return False
    
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return (intersection / union) >= threshold


def artist_matches(source: str, target: str, threshold: float = 0.6) -> bool:
    """
    Check if two artist names match (fuzzy comparison).
    Handles collaborations, features, special characters.
    """
    norm_source = normalize_artist(source)
    norm_target = normalize_artist(target)
    
    if not norm_source or not norm_target:
        return False
    
    # Exact match
    if norm_source == norm_target:
        return True
    
    # One contains the other
    if norm_source in norm_target or norm_target in norm_source:
        return True
    
    # Word-based Jaccard similarity
    words_source = set(norm_source.split())
    words_target = set(norm_target.split())
    
    if not words_source or not words_target:
        return False
    
    intersection = len(words_source & words_target)
    union = len(words_source | words_target)
    
    return (intersection / union) >= threshold


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


def split_artists(artist_string: str) -> list[str]:
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

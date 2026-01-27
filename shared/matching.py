"""
TG Player - Text Normalization and Matching Utilities

Consolidated module for all text normalization and fuzzy matching.
Used by: enrichment, album assembly, search, deduplication.
"""
import re
import unicodedata
from typing import Optional, List, Tuple
from functools import lru_cache


# ============== Constants ==============

# Threshold for fuzzy matching (0.0 to 1.0)
ARTIST_MATCH_THRESHOLD = 0.75
TITLE_MATCH_THRESHOLD = 0.6
ALBUM_MATCH_THRESHOLD = 0.7

# Common genre mappings
GENRE_MAPPINGS = {
    "rock": "Rock",
    "pop": "Pop",
    "hip hop": "Hip-Hop",
    "hip-hop": "Hip-Hop",
    "rap": "Hip-Hop",
    "electronic": "Electronic",
    "edm": "Electronic",
    "house": "Electronic",
    "techno": "Electronic",
    "dubstep": "Electronic",
    "dnb": "Drum & Bass",
    "drum and bass": "Drum & Bass",
    "jazz": "Jazz",
    "blues": "Blues",
    "classical": "Classical",
    "metal": "Metal",
    "punk": "Punk",
    "r&b": "R&B",
    "rnb": "R&B",
    "soul": "Soul",
    "country": "Country",
    "folk": "Folk",
    "indie": "Indie",
    "alternative": "Alternative",
    "reggae": "Reggae",
    "latin": "Latin",
    "world": "World",
    "ambient": "Ambient",
    "soundtrack": "Soundtrack",
    "k-pop": "K-Pop",
    "kpop": "K-Pop",
    "j-pop": "J-Pop",
    "jpop": "J-Pop",
    "russian": "Russian",
    "russian rap": "Russian Hip-Hop",
    "trap": "Trap",
    "drill": "Drill",
    "cloud rap": "Cloud Rap",
    "witch house": "Witch House",
}


# ============== Basic Normalization ==============

def normalize_unicode(text: str) -> str:
    """
    Normalize unicode characters.
    Converts curly quotes, special chars, etc. to ASCII equivalents.
    """
    if not text:
        return ""
    
    # NFKD normalization
    text = unicodedata.normalize('NFKD', text)
    
    # Common character replacements
    replacements = {
        '€': 'e', '$': 's', '@': 'a',
        ''': "'", ''': "'", '`': "'",
        '"': '"', '"': '"',
        '–': '-', '—': '-',
        '…': '...',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text


def remove_parenthetical(text: str) -> str:
    """
    Remove content in parentheses and brackets.
    Handles nested brackets with multiple passes.
    
    Examples:
        "Track (feat. Artist)" -> "Track"
        "Album ((Deluxe Edition))" -> "Album"
    """
    if not text:
        return ""
    
    # Multiple passes for nested brackets
    for _ in range(3):
        text = re.sub(r'\s*[\(\[][^\(\)\[\]]*[\)\]]', '', text)
    
    return text.strip()


def remove_featuring(text: str) -> str:
    """
    Remove featuring, prod, vs and everything after.
    
    Examples:
        "Track feat. Artist" -> "Track"
        "Song prod. Producer" -> "Song"
    """
    if not text:
        return ""
    
    patterns = [
        r'\s*(feat\.?|ft\.?|featuring)\s+.*$',
        r'\s*(prod\.?|produced\s+by)\s+.*$',
        r'\s*vs\.?\s+.*$',
    ]
    
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text.strip()


def extract_featured_artists(title: str, main_artist: Optional[str] = None) -> List[str]:
    """
    Extract featured/remix/prod artists from track title.
    
    Examples:
        "X Rated (Space Laces Remix)" -> ["Space Laces"]
        "Track feat. Artist1 & Artist2" -> ["Artist1", "Artist2"]
        "Song (Prod. Producer)" -> ["Producer"]
        "Battle vs. Other" -> ["Other"]
    
    Returns:
        List of additional artist names
    """
    if not title:
        return []
    
    artists = []
    
    # Pattern for remix: "(Artist Remix)" or "(Artist's Remix)" or "[Artist Remix]"
    remix_patterns = [
        r'[\(\[]([^\)\]]+?)(?:\'s)?\s+(?:Remix|Rmx|Mix|Edit|Bootleg|Rework|Flip|VIP)[\)\]]',
        r'\(Remix\s+by\s+([^\)]+)\)',
        r'\[Remix\s+by\s+([^\]]+)\]',
    ]
    for pattern in remix_patterns:
        matches = re.findall(pattern, title, flags=re.IGNORECASE)
        for match in matches:
            artist = match.strip()
            if artist and len(artist) > 1:
                artists.append(artist)
    
    # Pattern for feat.: "feat. Artist" or "ft. Artist"
    feat_match = re.search(r'(?:feat\.?|ft\.?|featuring)\s+([^\(\)\[\]]+?)(?:\s*[\(\[]|$)', title, flags=re.IGNORECASE)
    if feat_match:
        feat_part = feat_match.group(1).strip()
        # Split by & , and
        feat_artists = re.split(r'\s*(?:&|,|\band\b)\s*', feat_part)
        for fa in feat_artists:
            fa = fa.strip()
            if fa and len(fa) > 1:
                artists.append(fa)
    
    # Pattern for prod: "prod. Producer" or "(Prod. by Producer)"
    prod_patterns = [
        r'(?:prod\.?|produced\s+by)\s+([^\(\)\[\]]+?)(?:\s*[\(\[]|$)',
        r'[\(\[](?:prod\.?|produced\s+by)\s+([^\)\]]+)[\)\]]',
    ]
    for pattern in prod_patterns:
        matches = re.findall(pattern, title, flags=re.IGNORECASE)
        for match in matches:
            artist = match.strip()
            if artist and len(artist) > 1:
                artists.append(artist)
    
    # Pattern for vs: "vs. Artist" or "vs Artist"
    vs_match = re.search(r'\bvs\.?\s+([^\(\)\[\]]+?)(?:\s*[\(\[]|$)', title, flags=re.IGNORECASE)
    if vs_match:
        artist = vs_match.group(1).strip()
        if artist and len(artist) > 1:
            artists.append(artist)
    
    # Clean up: remove duplicates and main artist
    main_artist_lower = main_artist.lower() if main_artist else None
    unique = []
    seen = set()
    for a in artists:
        a_lower = a.lower()
        if a_lower not in seen and (not main_artist_lower or a_lower != main_artist_lower):
            seen.add(a_lower)
            unique.append(a)
    
    return unique


# ============== Artist Normalization ==============

@lru_cache(maxsize=1000)
def normalize_artist(artist: str) -> str:
    """
    Normalize artist name for matching and grouping.
    
    - Takes first artist from collaborations
    - Removes feat./prod. suffixes
    - Removes "и др." (Russian for "and others")
    - Normalizes case and special chars
    
    Examples:
        "A$AP Rocky" -> "asap rocky"
        "Drake, Future" -> "drake"
        "Artist feat. Other" -> "artist"
        "BLADEE и др." -> "bladee"
    """
    if not artist:
        return ""
    
    artist = normalize_unicode(artist).lower()
    artist = remove_parenthetical(artist)
    artist = remove_featuring(artist)
    
    # Remove Russian "и др." / "и другие" (and others)
    artist = re.sub(r'\s+и\s+др\.?$', '', artist, flags=re.IGNORECASE)
    artist = re.sub(r'\s+и\s+други[ех]?$', '', artist, flags=re.IGNORECASE)
    
    # Take first artist from collaborations
    # Separators: comma, ampersand, plus, x, and, with
    artist = re.split(r'\s*[,&+]\s*|\s+(?:x|and|with)\s+', artist, flags=re.IGNORECASE)[0]
    
    # Replace $ with s (A$AP -> ASAP)
    artist = artist.replace('$', 's')
    
    # Remove remaining special characters
    artist = re.sub(r'[^\w\s]', '', artist)
    
    # Normalize whitespace
    artist = ' '.join(artist.split())
    
    return artist.strip()


def normalize_artist_display(artist: str) -> str:
    """
    Normalize artist for display (keeps case, first artist only).
    
    Examples:
        "Drake, Future" -> "Drake"
        "Artist feat. Other" -> "Artist"
    """
    if not artist:
        return ""
    
    artist = remove_parenthetical(artist)
    artist = remove_featuring(artist)
    artist = re.split(r'\s*[,&+]\s*|\s+(?:x|and|with)\s+', artist, flags=re.IGNORECASE)[0]
    
    return artist.strip()


# ============== Title Normalization ==============

@lru_cache(maxsize=1000)
def normalize_title(title: str) -> str:
    """
    Normalize track title for matching.
    
    - Removes parenthetical content (feat., remix, etc.)
    - Normalizes unicode and case
    - Removes special characters
    
    Examples:
        "Track (Remix)" -> "track"
        "Song ft. Artist" -> "song"
    """
    if not title:
        return ""
    
    title = normalize_unicode(title).lower()
    title = remove_parenthetical(title)
    title = remove_featuring(title)
    
    # Remove apostrophes completely for matching
    title = title.replace("'", "")
    
    # Remove special characters, keep letters/numbers/spaces
    title = re.sub(r'[^\w\s]', '', title)
    
    # Normalize whitespace
    title = ' '.join(title.split())
    
    return title.strip()


# ============== Album Normalization ==============

# Important suffixes that make albums distinct
ALBUM_IMPORTANT_SUFFIXES = [
    r'\(deluxe[^)]*\)',
    r'\(remaster(?:ed)?[^)]*\)',
    r'\(expanded[^)]*\)',
    r'\(anniversary[^)]*\)',
    r'\(bonus[^)]*\)',
    r'\[deluxe[^\]]*\]',
    r'\[remaster(?:ed)?[^\]]*\]',
]


@lru_cache(maxsize=500)
def normalize_album(album: str) -> str:
    """
    Normalize album name for matching/grouping.
    Preserves important suffixes like (Deluxe), (Remastered).
    
    Examples:
        "D&G" -> "dg"
        "Album (Deluxe)" -> "album deluxe"
        " ICEDANCER " -> "icedancer"
    """
    if not album:
        return ""
    
    album = normalize_unicode(album).lower().strip()
    
    # Extract important suffixes BEFORE cleaning
    suffixes = []
    for pattern in ALBUM_IMPORTANT_SUFFIXES:
        match = re.search(pattern, album, re.IGNORECASE)
        if match:
            suffix = re.sub(r'[\(\)\[\]]', '', match.group()).strip()
            suffix = suffix.split()[0]  # "deluxe edition" -> "deluxe"
            suffixes.append(suffix)
    
    # Remove ALL parenthetical content
    album = remove_parenthetical(album)
    
    # Replace & with nothing (D&G = DG)
    album = album.replace('&', '')
    album = album.replace('$', 's')
    
    # Remove special characters
    album = re.sub(r'[^\w\s]', '', album)
    
    # Normalize whitespace
    album = ' '.join(album.split())
    
    # Add back important suffixes
    if suffixes:
        album = album + ' ' + ' '.join(sorted(set(suffixes)))
    
    return album.strip()


# ============== Search Query Cleaning ==============

def clean_for_search(text: str) -> str:
    """
    Clean text for external API search queries.
    More aggressive than normalization - removes noise for better API results.
    
    Examples:
        "Track (feat. Artist) [Remaster]" -> "Track"
        "guardianAngels((NO2))" -> "guardian Angels"
    """
    if not text:
        return ""
    
    text = normalize_unicode(text)
    
    # Add spaces before capitals in camelCase
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    
    # Remove parenthetical content
    text = remove_parenthetical(text)
    
    # Remove prod./feat.
    text = remove_featuring(text)
    
    # Remove trailing special characters
    text = re.sub(r'[\s\-_\.,;:]+$', '', text)
    
    return text.strip()


# ============== Fuzzy Matching ==============

def jaccard_similarity(set1: set, set2: set) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    return intersection / union if union > 0 else 0.0


def fuzzy_match_title(title1: str, title2: str) -> float:
    """
    Calculate similarity between two titles (0.0 to 1.0).
    Uses normalized comparison and word-based matching.
    
    Returns:
        Similarity score (0.0 to 1.0)
    """
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    
    if not norm1 or not norm2:
        return 0.0
    
    # Exact match after normalization
    if norm1 == norm2:
        return 1.0
    
    # Compare without spaces
    compact1 = norm1.replace(" ", "")
    compact2 = norm2.replace(" ", "")
    
    if compact1 == compact2:
        return 1.0
    
    # One contains the other
    if norm1 in norm2 or norm2 in norm1:
        return 0.9
    
    if compact1 in compact2 or compact2 in compact1:
        return 0.85
    
    # Word-based Jaccard similarity
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    base_similarity = jaccard_similarity(words1, words2)
    
    # Bonus for matching significant words (longer than 3 chars)
    significant1 = {w for w in words1 if len(w) > 3}
    significant2 = {w for w in words2 if len(w) > 3}
    
    if significant1 and significant2:
        sig_similarity = jaccard_similarity(significant1, significant2)
        # Weight significant words more heavily
        return max(base_similarity, sig_similarity * 0.95)
    
    return base_similarity


def fuzzy_match_artist(artist1: str, artist2: str) -> float:
    """
    Calculate similarity between two artist names (0.0 to 1.0).
    More strict than title matching.
    """
    norm1 = normalize_artist(artist1)
    norm2 = normalize_artist(artist2)
    
    if not norm1 or not norm2:
        return 0.0
    
    # Exact match
    if norm1 == norm2:
        return 1.0
    
    # Without spaces
    compact1 = norm1.replace(" ", "")
    compact2 = norm2.replace(" ", "")
    
    if compact1 == compact2:
        return 1.0
    
    # One contains the other (common for artist name variations)
    if norm1 in norm2 or norm2 in norm1:
        len_ratio = min(len(norm1), len(norm2)) / max(len(norm1), len(norm2))
        return 0.8 + (0.15 * len_ratio)
    
    # Word-based matching
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    return jaccard_similarity(words1, words2)


def fuzzy_match_album(album1: str, album2: str) -> float:
    """
    Calculate similarity between two album names (0.0 to 1.0).
    Similar to title matching but with album-specific adjustments.
    """
    norm1 = normalize_title(album1)
    norm2 = normalize_title(album2)
    
    if not norm1 or not norm2:
        return 0.0
    
    # Exact match
    if norm1 == norm2:
        return 1.0
    
    # Without spaces
    compact1 = norm1.replace(" ", "")
    compact2 = norm2.replace(" ", "")
    
    if compact1 == compact2:
        return 1.0
    
    # Word-based matching
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    return jaccard_similarity(words1, words2)


def albums_match(album1: str, album2: str, threshold: float = ALBUM_MATCH_THRESHOLD) -> bool:
    """Check if two album names match above threshold."""
    return fuzzy_match_album(album1, album2) >= threshold


def artists_match(artist1: str, artist2: str, threshold: float = ARTIST_MATCH_THRESHOLD) -> bool:
    """Check if two artist names match above threshold."""
    return fuzzy_match_artist(artist1, artist2) >= threshold


def titles_match(title1: str, title2: str, threshold: float = TITLE_MATCH_THRESHOLD) -> bool:
    """Check if two titles match above threshold."""
    return fuzzy_match_title(title1, title2) >= threshold


# ============== Genre Normalization ==============

def normalize_genre(genre: str) -> Optional[str]:
    """
    Normalize genre to standard form.
    Returns None if genre is not recognized.
    
    Examples:
        "hip hop" -> "Hip-Hop"
        "rnb" -> "R&B"
    """
    if not genre:
        return None
    
    genre_lower = genre.lower().strip()
    
    # Direct mapping
    if genre_lower in GENRE_MAPPINGS:
        return GENRE_MAPPINGS[genre_lower]
    
    # Check if contains any known genre
    for key, value in GENRE_MAPPINGS.items():
        if key in genre_lower:
            return value
    
    # Return original with title case if not mapped
    return genre.strip().title()


# ============== Input Sanitization ==============

def sanitize_input(value: str, max_length: int = 200) -> str:
    """
    Sanitize user input to prevent SQL injection.
    Use for search queries, filters, and user-provided strings.
    """
    if not value:
        return ""
    
    # Escape SQL wildcards
    value = value.replace('%', r'\%').replace('_', r'\_')
    
    return value[:max_length].strip()


def sanitize_search_query(query: str, max_length: int = 100) -> str:
    """
    Sanitize search input - more aggressive.
    Removes SQL special characters.
    """
    if not query:
        return ""
    
    # Remove SQL special characters
    query = re.sub(r'[;\'"\\%_]', '', query)
    
    return query[:max_length].strip()


# ============== Hashtag Generation ==============

def generate_hashtags(
    artist: Optional[str] = None,
    title: Optional[str] = None,
    album: Optional[str] = None,
    genre: Optional[str] = None,
    extra_tags: Optional[List[str]] = None
) -> List[str]:
    """
    Generate hashtags for a track.
    Used for user channel messages.
    
    Returns:
        List of hashtags without # prefix
    """
    tags = []
    
    def artist_to_tag(name: str) -> Optional[str]:
        """Convert artist name to hashtag."""
        tag = name.replace('!', 'I').replace(' ', '')
        tag = re.sub(r'[^\w]', '', tag)
        return tag if tag and len(tag) > 1 else None
    
    if artist:
        # Keep original case, replace ! with I (common stylization), remove other special chars
        tag = artist_to_tag(artist)
        if tag:
            tags.append(tag)
    
    # Extract featured artists from title (remixers, feat., prod., vs.)
    if title:
        featured = extract_featured_artists(title, main_artist=artist)
        for fa in featured:
            tag = artist_to_tag(fa)
            if tag:
                tags.append(tag)
    
    if album:
        # Use full album name without spaces/special chars
        normalized = normalize_album(album)
        if normalized:
            tag = re.sub(r'[^\w]', '', normalized)
            # Skip generic/short tags
            if tag and len(tag) > 3 and tag.lower() not in ('single', 'album', 'the', 'vol'):
                tags.append(tag)
    
    if genre:
        normalized = normalize_genre(genre)
        if normalized:
            tag = re.sub(r'[^\w]', '', normalized.lower())
            if tag and len(tag) > 2:
                tags.append(tag)
    
    if extra_tags:
        for t in extra_tags:
            tag = re.sub(r'[^\w]', '', t.lower())
            if tag and len(tag) > 1:
                tags.append(tag)
    
    # Remove duplicates, preserve order
    seen = set()
    unique_tags = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)
    
    return unique_tags


def format_hashtags(tags: List[str]) -> str:
    """Format list of tags as hashtag string."""
    return ' '.join(f'#{tag}' for tag in tags)

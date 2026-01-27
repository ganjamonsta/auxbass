"""
TG Player API v2 - Artists Router

Artist-related endpoints.
Artists are not stored separately - derived from tracks.
Uses normalization to group variations (BLADEE, Bladee, Bladee & Ecco2k -> Bladee)
"""
import sys
import logging
from pathlib import Path
from typing import Optional, List
from collections import defaultdict

# Add parent directory to path for shared/bot imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.database import get_db
from shared.models import (
    Track, Album, AlbumTrack, UserLibrary
)
from shared.matching import normalize_artist

from bot.services.enrichment.lastfm import lastfm_client
from bot.services.metadata import metadata_service

from api.routers.auth import get_current_user
from api.schemas_v2.artists import (
    ArtistResponse,
    ArtistDetailResponse,
    ArtistsListResponse,
)
from api.schemas_v2.common import TelegramUser


logger = logging.getLogger(__name__)

router = APIRouter(tags=["Artists"])


def get_best_display_name(artist_names: list[str]) -> str:
    """
    Choose the best display name from a list of artist name variations.
    Prefers: Title case, no collaborations, shorter names.
    """
    if not artist_names:
        return ""
    
    best = artist_names[0]
    best_priority = 0
    
    for name in artist_names:
        priority = 0
        
        # Prefer title case (first letter uppercase)
        if name and name[0].isupper():
            priority += 2
        
        # Prefer names without collaboration markers
        has_collab = any(sep in name.lower() for sep in [' & ', ' + ', ' x ', ', ', ' feat', ' ft.'])
        if not has_collab:
            priority += 3
        
        # Prefer shorter names
        if len(name) < len(best):
            priority += 1
            
        if priority > best_priority:
            best = name
            best_priority = priority
    
    return best


@router.get("", response_model=ArtistsListResponse)
async def get_my_artists(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: str = Query("name", pattern="^(name|track_count|album_count|latest_release)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get artists from user's library with normalization.
    
    Artists are grouped by normalized name (case-insensitive, first artist from collabs).
    Example: "BLADEE", "Bladee", "Bladee & Ecco2k" -> one "Bladee" artist
    
    Sort options:
    - name: alphabetically
    - track_count: by number of tracks
    - album_count: by number of albums  
    - latest_release: by latest album release date
    """
    # Get all artist names from user's library
    query = (
        select(Track.artist)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
        .where(Track.artist.isnot(None))
        .where(Track.artist != "")
    )
    
    result = await db.execute(query)
    all_artists = [row[0] for row in result.all()]
    
    # Group by normalized name
    # Key: normalized_name -> list of original names
    artist_groups: dict[str, list[str]] = defaultdict(list)
    
    for artist in all_artists:
        normalized = normalize_artist(artist)
        if normalized:
            artist_groups[normalized].append(artist)
    
    # Pre-fetch all albums for counting and getting release dates
    albums_result = await db.execute(
        select(Album)
        .where(Album.artist.isnot(None))
    )
    all_albums = albums_result.scalars().all()
    
    # Build album lookup by normalized artist
    # normalized_artist -> list of albums
    albums_by_artist: dict[str, list] = defaultdict(list)
    for album in all_albums:
        norm = normalize_artist(album.artist)
        if norm:
            albums_by_artist[norm].append(album)
    
    # Build aggregated list with album info
    aggregated = []
    for normalized, names in artist_groups.items():
        display_name = get_best_display_name(names)
        track_count = len(names)
        
        # Get albums for this artist
        artist_albums = albums_by_artist.get(normalized, [])
        album_count = len(artist_albums)
        
        # Get latest release date
        latest_release = None
        for album in sorted(artist_albums, key=lambda a: a.release_date or "", reverse=True):
            if album.release_date:
                latest_release = album.release_date
                break
        
        aggregated.append({
            "normalized": normalized,
            "name": display_name,
            "track_count": track_count,
            "album_count": album_count,
            "latest_release_date": latest_release,
            "all_names": names,  # For cover lookup
            "albums": artist_albums,  # For cover lookup
        })
    
    # Apply search filter
    if search:
        search_lower = search.lower()
        aggregated = [
            a for a in aggregated 
            if search_lower in a["normalized"] or search_lower in a["name"].lower()
        ]
    
    total = len(aggregated)
    
    # Sort
    reverse = (sort_order == "desc")
    if sort_by == "track_count":
        aggregated.sort(key=lambda x: x["track_count"], reverse=reverse)
    elif sort_by == "album_count":
        aggregated.sort(key=lambda x: x["album_count"], reverse=reverse)
    elif sort_by == "latest_release":
        # Sort by latest release date (nulls last)
        aggregated.sort(
            key=lambda x: x["latest_release_date"] or "",
            reverse=reverse
        )
    else:  # name
        aggregated.sort(key=lambda x: x["name"].lower(), reverse=reverse)
    
    # Paginate using offset/limit
    page_items = aggregated[offset:offset + limit]
    
    # Calculate page for response (for backwards compatibility)
    page = (offset // limit) + 1 if limit > 0 else 1
    
    # Build response items with covers from pre-fetched albums
    items = []
    for artist_data in page_items:
        # Get cover from latest album (already sorted by release_date)
        cover_url = None
        for album in sorted(artist_data["albums"], key=lambda a: a.release_date or "", reverse=True):
            if album.cover_url:
                cover_url = album.cover_url
                break
        
        items.append(ArtistResponse(
            name=artist_data["name"],
            track_count=artist_data["track_count"],
            album_count=artist_data["album_count"],
            cover_url=cover_url,
            image_url=cover_url,  # Frontend compatibility
            latest_release_date=artist_data["latest_release_date"],
        ))
    
    return ArtistsListResponse(
        items=items,
        total=total,
        page=page,
        per_page=limit,
    )


# ============== Global Library ==============

@router.get("/global", response_model=ArtistsListResponse)
async def get_global_artists(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: str = Query("name", pattern="^(name|track_count|album_count|latest_release)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get artists from global public library.
    
    Shows all artists that have public tracks in the system.
    """
    # Get all artist names from public tracks
    query = (
        select(Track.artist)
        .where(Track.is_public == True)
        .where(Track.is_unavailable == False)
        .where(Track.artist.isnot(None))
        .where(Track.artist != "")
    )
    
    result = await db.execute(query)
    all_artists = [row[0] for row in result.all()]
    
    # Group by normalized name
    artist_groups: dict[str, list[str]] = defaultdict(list)
    
    for artist in all_artists:
        normalized = normalize_artist(artist)
        if normalized:
            artist_groups[normalized].append(artist)
    
    # Pre-fetch all albums for counting and getting release dates
    albums_result = await db.execute(
        select(Album)
        .where(Album.artist.isnot(None))
    )
    all_albums = albums_result.scalars().all()
    
    # Build album lookup by normalized artist
    albums_by_artist: dict[str, list] = defaultdict(list)
    for album in all_albums:
        norm = normalize_artist(album.artist)
        if norm:
            albums_by_artist[norm].append(album)
    
    # Build aggregated list with album info
    aggregated = []
    for normalized, names in artist_groups.items():
        display_name = get_best_display_name(names)
        track_count = len(names)
        
        artist_albums = albums_by_artist.get(normalized, [])
        album_count = len(artist_albums)
        
        latest_release = None
        for album in sorted(artist_albums, key=lambda a: a.release_date or "", reverse=True):
            if album.release_date:
                latest_release = album.release_date
                break
        
        aggregated.append({
            "normalized": normalized,
            "name": display_name,
            "track_count": track_count,
            "album_count": album_count,
            "latest_release_date": latest_release,
            "albums": artist_albums,
        })
    
    # Apply search filter
    if search:
        search_lower = search.lower()
        aggregated = [
            a for a in aggregated 
            if search_lower in a["normalized"] or search_lower in a["name"].lower()
        ]
    
    total = len(aggregated)
    
    # Sort
    reverse = (sort_order == "desc")
    if sort_by == "track_count":
        aggregated.sort(key=lambda x: x["track_count"], reverse=reverse)
    elif sort_by == "album_count":
        aggregated.sort(key=lambda x: x["album_count"], reverse=reverse)
    elif sort_by == "latest_release":
        aggregated.sort(
            key=lambda x: x["latest_release_date"] or "",
            reverse=reverse
        )
    else:  # name
        aggregated.sort(key=lambda x: x["name"].lower(), reverse=reverse)
    
    # Paginate
    page_items = aggregated[offset:offset + limit]
    page = (offset // limit) + 1 if limit > 0 else 1
    
    # Build response items
    items = []
    for artist_data in page_items:
        cover_url = None
        for album in sorted(artist_data["albums"], key=lambda a: a.release_date or "", reverse=True):
            if album.cover_url:
                cover_url = cover_url or album.cover_url
                break
        
        items.append(ArtistResponse(
            name=artist_data["name"],
            track_count=artist_data["track_count"],
            album_count=artist_data["album_count"],
            cover_url=cover_url,
            image_url=cover_url,
            latest_release_date=artist_data["latest_release_date"],
        ))
    
    return ArtistsListResponse(
        items=items,
        total=total,
        page=page,
        per_page=limit,
    )


@router.get("/{artist_name}", response_model=ArtistDetailResponse)
async def get_artist(
    artist_name: str,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get artist details with tracks and albums (matched by normalized name)"""
    normalized_search = normalize_artist(artist_name)
    
    # Get all tracks and filter by normalized artist
    tracks_result = await db.execute(
        select(Track, UserLibrary)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
        .where(Track.artist.isnot(None))
        .options(
            selectinload(Track.enrichment),
            selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
        )
        .order_by(UserLibrary.play_count.desc(), Track.title.asc())
    )
    all_tracks = tracks_result.unique().all()
    
    # Filter by normalized artist
    matching_tracks = []
    artist_names_seen = set()
    album_track_counts = {}  # album_id -> count
    
    for track, lib_entry in all_tracks:
        if normalize_artist(track.artist) == normalized_search:
            matching_tracks.append((track, lib_entry))
            artist_names_seen.add(track.artist)
            # Count tracks per album
            for at in track.album_tracks:
                album_track_counts[at.album_id] = album_track_counts.get(at.album_id, 0) + 1
    
    track_count = len(matching_tracks)
    
    if track_count == 0:
        raise HTTPException(status_code=404, detail="Artist not found in your library")
    
    # Get best display name
    actual_name = get_best_display_name(list(artist_names_seen)) or artist_name
    
    # Get albums by this artist (normalized)
    albums_result = await db.execute(
        select(Album)
        .where(Album.artist.isnot(None))
        .order_by(Album.release_date.desc().nullslast())
    )
    all_albums = albums_result.scalars().all()
    albums = [a for a in all_albums if normalize_artist(a.artist) == normalized_search]
    
    # Get cover URL from albums
    cover_url = None
    for album in albums:
        if album.cover_url:
            cover_url = album.cover_url
            break
    
    # All tracks (not just top 10)
    from api.routers.library import track_to_response
    all_tracks = [track_to_response(track, lib_entry) for track, lib_entry in matching_tracks]
    
    # Albums as response - pass track_count to avoid lazy loading
    from api.routers.albums import album_to_response
    album_items = [album_to_response(album, track_count=album_track_counts.get(album.id, 0)) for album in albums]
    
    return ArtistDetailResponse(
        name=actual_name,
        track_count=track_count,
        album_count=len(albums),
        cover_url=cover_url,
        image_url=cover_url,  # Frontend compatibility
        albums=album_items,
        tracks=all_tracks,
    )


@router.get("/{artist_name}/ids")
async def get_artist_track_ids(
    artist_name: str,
    shuffle: bool = False,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all track IDs for an artist.
    
    Lightweight endpoint for shuffle - returns only IDs.
    """
    normalized_search = normalize_artist(artist_name)
    
    query = (
        select(Track.id)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
        .where(Track.artist.isnot(None))
    )
    
    if shuffle:
        query = query.order_by(func.random())
    else:
        query = query.order_by(Track.title.asc())
    
    result = await db.execute(query)
    all_ids = result.scalars().all()
    
    # Need to filter by normalized artist - fetch artists for filtering
    artist_result = await db.execute(
        select(Track.id, Track.artist)
        .where(Track.id.in_(all_ids))
    )
    
    matching_ids = [
        row[0] for row in artist_result.all()
        if normalize_artist(row[1]) == normalized_search
    ]
    
    return {"ids": matching_ids, "total": len(matching_ids)}


# Last.fm placeholder image hash (indicates no real image)
LASTFM_PLACEHOLDER_HASH = "2a96cbd8b46e442fc41c2b86b821562f"


@router.get("/{artist_name}/image")
async def get_artist_image(
    artist_name: str,
    response: Response,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get artist image URL with fallback priority:
    1. Last.fm artist image
    2. Deezer artist picture
    3. Latest album cover from library (by release_date)
    
    Returns: {"artist": str, "image_url": str | null, "source": str}
    """
    # Cache for 24 hours - artist images rarely change
    response.headers["Cache-Control"] = "public, max-age=86400, stale-while-revalidate=604800"
    
    normalized_search = normalize_artist(artist_name)
    
    # Priority 1: Try Last.fm
    try:
        if lastfm_client.is_configured:
            lastfm_info = await lastfm_client.get_artist_info(artist_name)
            if lastfm_info and lastfm_info.get("image_url"):
                image_url = lastfm_info["image_url"]
                # Check if it's not the Last.fm placeholder image
                if LASTFM_PLACEHOLDER_HASH not in image_url:
                    logger.debug(f"Artist image from Last.fm: {artist_name}")
                    return {
                        "artist": artist_name,
                        "image_url": image_url,
                        "source": "lastfm"
                    }
    except Exception as e:
        logger.warning(f"Last.fm artist lookup failed: {e}")
    
    # Priority 2: Try Deezer
    try:
        deezer_info = await metadata_service.search_deezer_artist(artist_name)
        if deezer_info and deezer_info.get("picture_url"):
            logger.debug(f"Artist image from Deezer: {artist_name}")
            return {
                "artist": artist_name,
                "image_url": deezer_info["picture_url"],
                "source": "deezer"
            }
    except Exception as e:
        logger.warning(f"Deezer artist lookup failed: {e}")
    
    # Priority 3: Latest album cover from library (by release_date)
    try:
        # Get all albums for this artist, sorted by release_date desc
        albums_result = await db.execute(
            select(Album)
            .where(Album.cover_url.isnot(None))
            .where(Album.release_date.isnot(None))
            .order_by(Album.release_date.desc())
        )
        all_albums = albums_result.scalars().all()
        
        # Find albums matching this artist
        for album in all_albums:
            if normalize_artist(album.artist) == normalized_search:
                logger.debug(f"Artist image from album '{album.name}': {artist_name}")
                return {
                    "artist": artist_name,
                    "image_url": album.cover_url,
                    "source": "album",
                    "album_name": album.name
                }
        
        # Also try albums without release_date as last resort
        albums_no_date = await db.execute(
            select(Album)
            .where(Album.cover_url.isnot(None))
            .where(Album.release_date.is_(None))
        )
        for album in albums_no_date.scalars().all():
            if normalize_artist(album.artist) == normalized_search:
                logger.debug(f"Artist image from album (no date) '{album.name}': {artist_name}")
                return {
                    "artist": artist_name,
                    "image_url": album.cover_url,
                    "source": "album",
                    "album_name": album.name
                }
    except Exception as e:
        logger.warning(f"Album cover lookup failed: {e}")
    
    # No image found
    return {
        "artist": artist_name,
        "image_url": None,
        "source": None
    }

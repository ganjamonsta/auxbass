"""
TG Player API v2 - Artists Router

Artist-related endpoints.
Artists are not stored separately - derived from tracks.
Uses normalization to group variations (BLADEE, Bladee, Bladee & Ecco2k -> Bladee)
"""
import sys
import logging
import re
from pathlib import Path
from typing import Optional, List
from collections import defaultdict
from urllib.parse import unquote

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
from shared.matching import normalize_artist, normalize_artist_display, extract_featured_artists, get_all_track_artists, extract_artists_from_filename

from bot.services.enrichment.lastfm import lastfm_client
from bot.services.metadata import metadata_service

from api.routers.auth import get_current_user
from api.schemas.artists import (
    ArtistResponse,
    ArtistDetailResponse,
    ArtistInfoResponse,
    ArtistTracksResponse,
    ArtistsListResponse,
)
from api.schemas.common import TelegramUser


logger = logging.getLogger(__name__)

router = APIRouter(tags=["Artists"])


def artist_matches_track(track_artist: str, normalized_search: str, track_title: str = None, track_file_name: str = None) -> bool:
    """
    Check if normalized search artist is present in track artist string, title, or filename.
    Handles 'Artist A feat. Artist B', 'Artist A & Artist C', etc.
    Also checks file_name for tracks without metadata.
    """
    # 1. Check artist field
    if track_artist:
        # Quick check using standard normalization
        if normalize_artist(track_artist) == normalized_search:
            return True
            
        # Check parts: split by common separators
        parts = re.split(r'\s*(?:,|&|\+|\bx\b|\band\b|\bwith\b|feat\.?|ft\.?|featuring|prod\.?|produced\s+by|vs\.?)\s*', track_artist, flags=re.IGNORECASE)
        
        for part in parts:
            if part and normalize_artist(part) == normalized_search:
                return True

    # 2. Check title field for featuring/prod/remix
    if track_title:
        extracted = extract_featured_artists(track_title)
        for artist in extracted:
            if normalize_artist(artist) == normalized_search:
                return True
    
    # 3. Check file_name for tracks without metadata (or as fallback)
    if track_file_name:
        extracted = extract_artists_from_filename(track_file_name)
        for artist in extracted:
            if normalize_artist(artist) == normalized_search:
                return True
                
    return False


def get_best_display_name(artist_names: list[str]) -> str:
    """
    Choose the best display name from a list of artist name variations.
    Prefers: Title case, no collaborations, shorter names.
    Returns only the first artist (no collaborators).
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
    
    # Always return only the first artist (strip collaborations)
    return normalize_artist_display(best)


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
    
    Optimized: album data is loaded only when needed for sorting/display.
    
    Sort options:
    - name: alphabetically
    - track_count: by number of tracks
    - album_count: by number of albums  
    - latest_release: by latest album release date
    """
    # Get all tracks from user's library (lightweight query)
    query = (
        select(Track.artist, Track.title, Track.file_name)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
    )
    
    result = await db.execute(query)
    all_tracks_data = result.all()
    
    # Group by normalized name
    artist_groups: dict[str, list[str]] = defaultdict(list)
    
    for track_artist, track_title, track_file_name in all_tracks_data:
        all_artists = get_all_track_artists(track_artist, track_title, track_file_name)
        
        for artist in all_artists:
            normalized = normalize_artist(artist)
            if normalized:
                artist_groups[normalized].append(artist)
    
    # Build basic aggregated list
    aggregated = []
    for normalized, names in artist_groups.items():
        display_name = get_best_display_name(names)
        track_count = len(names)
        
        aggregated.append({
            "normalized": normalized,
            "name": display_name,
            "track_count": track_count,
            "album_count": 0,  # Lazy loaded
            "latest_release_date": None,  # Lazy loaded
            "albums": [],  # Lazy loaded
        })
    
    # Apply search filter early (before expensive album lookups)
    if search:
        search_lower = search.lower()
        aggregated = [
            a for a in aggregated 
            if search_lower in a["normalized"] or search_lower in a["name"].lower()
        ]
    
    total = len(aggregated)
    
    # Only load album data if we need it for sorting or display
    needs_album_data = sort_by in ("album_count", "latest_release")
    
    if needs_album_data:  # Only query albums when actually needed
        # Get album counts and latest dates efficiently with a single query
        # Only for artists we'll actually display (after pagination for simple sorts)
        
        # For album-based sorts, we need all artists' album data first
        if sort_by in ("album_count", "latest_release"):
            normalized_artists = [a["normalized"] for a in aggregated]
        else:
            # For name/track_count sorts, pre-sort and get only page artists
            reverse = (sort_order == "desc")
            if sort_by == "track_count":
                aggregated.sort(key=lambda x: x["track_count"], reverse=reverse)
            else:  # name
                aggregated.sort(key=lambda x: x["name"].lower(), reverse=reverse)
            
            page_items_presort = aggregated[offset:offset + limit]
            normalized_artists = [a["normalized"] for a in page_items_presort]
        
        # Load albums only for relevant artists
        if normalized_artists:
            albums_result = await db.execute(
                select(Album)
                .where(Album.artist.isnot(None))
            )
            all_albums = albums_result.scalars().all()
            
            # Build album lookup
            albums_by_artist: dict[str, list] = defaultdict(list)
            for album in all_albums:
                norm = normalize_artist(album.artist)
                if norm in normalized_artists or sort_by in ("album_count", "latest_release"):
                    albums_by_artist[norm].append(album)
            
            # Update aggregated with album data
            for item in aggregated:
                artist_albums = albums_by_artist.get(item["normalized"], [])
                item["album_count"] = len(artist_albums)
                item["albums"] = artist_albums
                
                # Get latest release date
                for album in sorted(artist_albums, key=lambda a: a.release_date or "", reverse=True):
                    if album.release_date:
                        item["latest_release_date"] = album.release_date
                        break
    
    # Sort (if album-based sort, do it now after loading album data)
    # Use secondary sort by name for stable pagination
    reverse = (sort_order == "desc")
    if sort_by == "album_count":
        aggregated.sort(key=lambda x: (x["album_count"], x["name"].lower()), reverse=reverse)
    elif sort_by == "latest_release":
        aggregated.sort(key=lambda x: (x["latest_release_date"] or "", x["name"].lower()), reverse=reverse)
    elif sort_by == "track_count":
        aggregated.sort(key=lambda x: (x["track_count"], x["name"].lower()), reverse=reverse)
    else:  # name
        aggregated.sort(key=lambda x: x["name"].lower(), reverse=reverse)
    
    # Paginate
    page_items = aggregated[offset:offset + limit]
    page = (offset // limit) + 1 if limit > 0 else 1
    
    # Build response
    items = []
    for artist_data in page_items:
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
            image_url=cover_url,
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
    Also includes artists extracted from track titles and filenames.
    """
    # Get all tracks from public library (including those without artist metadata)
    query = (
        select(Track.artist, Track.title, Track.file_name)
        .where(Track.is_public == True)
        .where(Track.is_unavailable == False)
    )
    
    result = await db.execute(query)
    all_tracks_data = result.all()
    
    # Group by normalized name
    artist_groups: dict[str, list[str]] = defaultdict(list)
    
    for track_artist, track_title, track_file_name in all_tracks_data:
        # Get all artists from this track (from artist, title, file_name)
        all_artists = get_all_track_artists(track_artist, track_title, track_file_name)
        
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
    
    # Sort - use secondary sort by name for stable pagination
    reverse = (sort_order == "desc")
    if sort_by == "track_count":
        aggregated.sort(key=lambda x: (x["track_count"], x["name"].lower()), reverse=reverse)
    elif sort_by == "album_count":
        aggregated.sort(key=lambda x: (x["album_count"], x["name"].lower()), reverse=reverse)
    elif sort_by == "latest_release":
        aggregated.sort(
            key=lambda x: (x["latest_release_date"] or "", x["name"].lower()),
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


@router.get("/{artist_name}/info", response_model=ArtistInfoResponse)
async def get_artist_info(
    artist_name: str,
    scope: str = Query("library", pattern="^(library|global)$"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get artist info WITHOUT tracks (lightweight endpoint for initial page load).
    
    Returns artist metadata, album list, and track count.
    Use /artists/{artist_name}/tracks for paginated tracks.
    
    Optimized: Uses SQL filtering on normalized_artist column.
    """
    artist_name = unquote(artist_name)
    normalized_search = normalize_artist(artist_name)
    
    # Optimized: Count tracks using SQL filter on normalized_artist
    if scope == "global":
        count_result = await db.execute(
            select(func.count(Track.id))
            .where(Track.is_public == True)
            .where(Track.is_unavailable == False)
            .where(Track.normalized_artist == normalized_search)
        )
        track_count = count_result.scalar() or 0
        
        # Get sample artist name for display
        sample_result = await db.execute(
            select(Track.artist)
            .where(Track.is_public == True)
            .where(Track.is_unavailable == False)
            .where(Track.normalized_artist == normalized_search)
            .limit(1)
        )
        sample_artist = sample_result.scalar()
        
        # Get track IDs for album counting (limited for performance)
        track_ids_result = await db.execute(
            select(Track.id)
            .where(Track.is_public == True)
            .where(Track.is_unavailable == False)
            .where(Track.normalized_artist == normalized_search)
        )
        album_track_ids = set(row[0] for row in track_ids_result.all())
    else:
        count_result = await db.execute(
            select(func.count(Track.id))
            .join(UserLibrary, UserLibrary.track_id == Track.id)
            .where(UserLibrary.user_id == user.id)
            .where(Track.normalized_artist == normalized_search)
        )
        track_count = count_result.scalar() or 0
        
        # Get sample artist name for display
        sample_result = await db.execute(
            select(Track.artist)
            .join(UserLibrary, UserLibrary.track_id == Track.id)
            .where(UserLibrary.user_id == user.id)
            .where(Track.normalized_artist == normalized_search)
            .limit(1)
        )
        sample_artist = sample_result.scalar()
        
        # Get track IDs for album counting
        track_ids_result = await db.execute(
            select(Track.id)
            .join(UserLibrary, UserLibrary.track_id == Track.id)
            .where(UserLibrary.user_id == user.id)
            .where(Track.normalized_artist == normalized_search)
        )
        album_track_ids = set(row[0] for row in track_ids_result.all())
    
    if track_count == 0:
        detail = "Artist not found" if scope == "global" else "Artist not found in your library"
        raise HTTPException(status_code=404, detail=detail)
    
    # Determine display name
    actual_name = normalize_artist_display(sample_artist) if sample_artist else artist_name
    
    # Get albums efficiently - only those with tracks in this scope
    album_track_counts = {}
    if album_track_ids:
        album_tracks_result = await db.execute(
            select(AlbumTrack.album_id, func.count(AlbumTrack.track_id))
            .where(AlbumTrack.track_id.in_(album_track_ids))
            .group_by(AlbumTrack.album_id)
        )
        album_track_counts = {row[0]: row[1] for row in album_tracks_result.all()}
    
    # Get albums for this artist
    if album_track_counts:
        albums_result = await db.execute(
            select(Album)
            .where(Album.id.in_(album_track_counts.keys()))
            .order_by(Album.release_date.desc().nullslast())
        )
        albums = albums_result.scalars().all()
    else:
        # Fallback: get albums by normalized_artist (if Album has it)
        albums_result = await db.execute(
            select(Album)
            .where(Album.normalized_artist == normalized_search)
            .order_by(Album.release_date.desc().nullslast())
        )
        albums = albums_result.scalars().all()
    
    # Get cover URL
    cover_url = None
    for album in albums:
        if album.cover_url:
            cover_url = album.cover_url
            break
    
    # Get artist tags (async, non-blocking for initial load)
    artist_tags = None
    try:
        if lastfm_client.is_configured:
            artist_tags = await lastfm_client.get_artist_top_tags(actual_name)
    except Exception as e:
        logger.warning(f"Failed to get artist tags: {e}")
    
    from api.routers.albums import album_to_response
    album_items = [album_to_response(album, track_count=album_track_counts.get(album.id, 0)) 
                   for album in albums]
    
    return ArtistInfoResponse(
        name=actual_name,
        track_count=track_count,
        album_count=len(albums),
        cover_url=cover_url,
        image_url=cover_url,
        tags=artist_tags,
        albums=album_items,
    )


@router.get("/{artist_name}", response_model=ArtistDetailResponse)
async def get_artist(
    artist_name: str,
    scope: str = Query("library", pattern="^(library|global)$"),
    include_tracks: bool = Query(False, description="Include all tracks (legacy mode, use /tracks endpoint instead)"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get artist details.
    
    By default, returns artist info WITHOUT tracks for performance.
    Use include_tracks=true for legacy behavior (all tracks in one response).
    
    RECOMMENDED: Use /{artist_name}/info + /{artist_name}/tracks for best performance.
    
    scope=library: only user's library tracks
    scope=global: all public tracks
    """
    artist_name = unquote(artist_name)
    normalized_search = normalize_artist(artist_name)
    
    # For performance: if not including tracks, use lightweight query
    if not include_tracks:
        # Get info without tracks
        info = await get_artist_info(artist_name, scope, user, db)
        return ArtistDetailResponse(
            name=info.name,
            track_count=info.track_count,
            album_count=info.album_count,
            cover_url=info.cover_url,
            image_url=info.image_url,
            tags=info.tags,
            albums=info.albums,
            tracks=[],  # Empty - use /tracks endpoint for paginated loading
        )
    
    # Legacy mode: include all tracks (not recommended for large libraries)
    # Optimized: Use SQL filter on normalized_artist
    if scope == "global":
        tracks_result = await db.execute(
            select(Track)
            .where(Track.is_public == True)
            .where(Track.is_unavailable == False)
            .where(Track.normalized_artist == normalized_search)
            .options(
                selectinload(Track.enrichment),
                selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
            )
            .order_by(Track.created_at.desc())
        )
        matching_tracks = list(tracks_result.unique().scalars().all())
        
        track_count = len(matching_tracks)
        
        if track_count == 0:
            raise HTTPException(status_code=404, detail="Artist not found")
        
        # Get album track counts
        album_track_counts = {}
        for track in matching_tracks:
            for at in track.album_tracks:
                album_track_counts[at.album_id] = album_track_counts.get(at.album_id, 0) + 1
        
        # Get sample artist name for display
        sample_artist = matching_tracks[0].artist if matching_tracks else None
        
        user_lib_result = await db.execute(
            select(UserLibrary.track_id)
            .where(UserLibrary.user_id == user.id)
        )
        user_library_ids = set(row[0] for row in user_lib_result.all())
        
        from api.routers.library import track_to_response_global
        all_tracks_response = [
            track_to_response_global(track, in_library=track.id in user_library_ids)
            for track in matching_tracks
        ]
    else:
        tracks_result = await db.execute(
            select(Track, UserLibrary)
            .join(UserLibrary, UserLibrary.track_id == Track.id)
            .where(UserLibrary.user_id == user.id)
            .where(Track.normalized_artist == normalized_search)
            .options(
                selectinload(Track.enrichment),
                selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
            )
            .order_by(UserLibrary.play_count.desc(), Track.title.asc())
        )
        matching_tracks = list(tracks_result.unique().all())
        
        track_count = len(matching_tracks)
        
        if track_count == 0:
            raise HTTPException(status_code=404, detail="Artist not found in your library")
        
        # Get album track counts
        album_track_counts = {}
        for track, _ in matching_tracks:
            for at in track.album_tracks:
                album_track_counts[at.album_id] = album_track_counts.get(at.album_id, 0) + 1
        
        # Get sample artist name for display
        sample_artist = matching_tracks[0][0].artist if matching_tracks else None
        
        from api.routers.library import track_to_response
        all_tracks_response = [track_to_response(track, lib_entry) for track, lib_entry in matching_tracks]
    
    actual_name = normalize_artist_display(sample_artist) if sample_artist else artist_name
    
    # Get albums using normalized_artist
    albums_result = await db.execute(
        select(Album)
        .where(Album.normalized_artist == normalized_search)
        .order_by(Album.release_date.desc().nullslast())
    )
    all_artist_albums = list(albums_result.scalars().all())
    
    if scope == "library":
        albums = [a for a in all_artist_albums if album_track_counts.get(a.id, 0) > 0]
    else:
        albums = all_artist_albums
    
    cover_url = None
    for album in albums:
        if album.cover_url:
            cover_url = album.cover_url
            break
    
    artist_tags = None
    try:
        if lastfm_client.is_configured:
            artist_tags = await lastfm_client.get_artist_top_tags(actual_name)
    except Exception as e:
        logger.warning(f"Failed to get artist tags: {e}")
    
    from api.routers.albums import album_to_response
    album_items = [album_to_response(album, track_count=album_track_counts.get(album.id, 0)) for album in albums]
    
    return ArtistDetailResponse(
        name=actual_name,
        track_count=track_count,
        album_count=len(albums),
        cover_url=cover_url,
        image_url=cover_url,
        tags=artist_tags,
        albums=album_items,
        tracks=all_tracks_response,
    )


@router.get("/{artist_name}/tracks", response_model=ArtistTracksResponse)
async def get_artist_tracks(
    artist_name: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    scope: str = Query("library", pattern="^(library|global)$"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated tracks for an artist.
    
    Optimized SQL-based filtering using normalized_artist column.
    Falls back to Python filtering only for tracks without normalized_artist.
    """
    artist_name = unquote(artist_name)
    normalized_search = normalize_artist(artist_name)
    
    # Try optimized SQL query first (using normalized_artist index)
    if scope == "global":
        # Count total matching tracks
        count_result = await db.execute(
            select(func.count(Track.id))
            .where(Track.is_public == True)
            .where(Track.is_unavailable == False)
            .where(Track.normalized_artist == normalized_search)
        )
        total = count_result.scalar() or 0
        
        # Get page of track IDs with SQL pagination
        ids_result = await db.execute(
            select(Track.id)
            .where(Track.is_public == True)
            .where(Track.is_unavailable == False)
            .where(Track.normalized_artist == normalized_search)
            .order_by(Track.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        page_ids = [row[0] for row in ids_result.all()]
    else:
        # Count total matching tracks in user's library
        count_result = await db.execute(
            select(func.count(Track.id))
            .join(UserLibrary, UserLibrary.track_id == Track.id)
            .where(UserLibrary.user_id == user.id)
            .where(Track.normalized_artist == normalized_search)
        )
        total = count_result.scalar() or 0
        
        # Get page of track IDs with SQL pagination
        ids_result = await db.execute(
            select(Track.id)
            .join(UserLibrary, UserLibrary.track_id == Track.id)
            .where(UserLibrary.user_id == user.id)
            .where(Track.normalized_artist == normalized_search)
            .order_by(UserLibrary.play_count.desc(), Track.title.asc())
            .offset(offset)
            .limit(limit)
        )
        page_ids = [row[0] for row in ids_result.all()]
    
    if not page_ids:
        return ArtistTracksResponse(
            items=[],
            total=total,
            offset=offset,
            limit=limit,
        )
    
    # Load full track data for the page
    if scope == "global":
        tracks_result = await db.execute(
            select(Track)
            .where(Track.id.in_(page_ids))
            .options(
                selectinload(Track.enrichment),
                selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
            )
        )
        tracks_map = {t.id: t for t in tracks_result.unique().scalars().all()}
        
        # Get user's library status for these tracks
        user_lib_result = await db.execute(
            select(UserLibrary.track_id)
            .where(UserLibrary.user_id == user.id)
            .where(UserLibrary.track_id.in_(page_ids))
        )
        user_library_ids = set(row[0] for row in user_lib_result.all())
        
        from api.routers.library import track_to_response_global
        # Preserve order from matching_ids
        tracks_response = [
            track_to_response_global(tracks_map[tid], in_library=tid in user_library_ids)
            for tid in page_ids if tid in tracks_map
        ]
    else:
        tracks_result = await db.execute(
            select(Track, UserLibrary)
            .join(UserLibrary, UserLibrary.track_id == Track.id)
            .where(Track.id.in_(page_ids))
            .where(UserLibrary.user_id == user.id)
            .options(
                selectinload(Track.enrichment),
                selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
            )
        )
        tracks_map = {t.id: (t, lib) for t, lib in tracks_result.unique().all()}
        
        from api.routers.library import track_to_response
        # Preserve order from matching_ids
        tracks_response = [
            track_to_response(tracks_map[tid][0], tracks_map[tid][1])
            for tid in page_ids if tid in tracks_map
        ]
    
    return ArtistTracksResponse(
        items=tracks_response,
        total=total,
        offset=offset,
        limit=limit,
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
    Optimized: Uses SQL filtering on normalized_artist column.
    """
    normalized_search = normalize_artist(artist_name)
    
    # Optimized: SQL filter on normalized_artist
    query = (
        select(Track.id)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
        .where(Track.normalized_artist == normalized_search)
    )
    
    if shuffle:
        query = query.order_by(func.random())
    else:
        query = query.order_by(Track.title.asc())
    
    result = await db.execute(query)
    matching_ids = list(result.scalars().all())
    
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
    # Optimized: Use normalized_artist column
    try:
        # Get albums matching this artist by normalized_artist, sorted by release_date desc
        albums_result = await db.execute(
            select(Album)
            .where(Album.cover_url.isnot(None))
            .where(Album.normalized_artist == normalized_search)
            .order_by(Album.release_date.desc().nullslast())
            .limit(1)
        )
        album = albums_result.scalars().first()
        
        if album:
            logger.debug(f"Artist image from album '{album.name}': {artist_name}")
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

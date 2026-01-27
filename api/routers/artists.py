"""
TG Player API v2 - Artists Router

Artist-related endpoints.
Artists are not stored separately - derived from tracks.
Uses normalization to group variations (BLADEE, Bladee, Bladee & Ecco2k -> Bladee)
"""
from typing import Optional, List
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import get_db
from shared.models import (
    Track, Album, AlbumTrack, UserLibrary
)
from shared.matching import normalize_artist

from api.routers.auth import get_current_user
from api.schemas_v2.artists import (
    ArtistResponse,
    ArtistDetailResponse,
    ArtistsListResponse,
)
from api.schemas_v2.common import TelegramUser


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
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: str = Query("name", pattern="^(name|track_count)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get artists from user's library with normalization.
    
    Artists are grouped by normalized name (case-insensitive, first artist from collabs).
    Example: "BLADEE", "Bladee", "Bladee & Ecco2k" -> one "Bladee" artist
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
    
    # Build aggregated list
    aggregated = []
    for normalized, names in artist_groups.items():
        display_name = get_best_display_name(names)
        track_count = len(names)
        
        aggregated.append({
            "normalized": normalized,
            "name": display_name,
            "track_count": track_count,
            "all_names": names,  # For cover lookup
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
    if sort_by == "track_count":
        aggregated.sort(key=lambda x: x["track_count"], reverse=(sort_order == "desc"))
    else:
        aggregated.sort(key=lambda x: x["name"].lower(), reverse=(sort_order == "desc"))
    
    # Paginate
    offset = (page - 1) * per_page
    page_items = aggregated[offset:offset + per_page]
    
    # Get covers for each artist
    items = []
    for artist_data in page_items:
        cover_url = None
        
        # Try to get cover from albums (check any matching artist name)
        for name in artist_data["all_names"][:5]:  # Limit lookups
            cover_result = await db.execute(
                select(Album.cover_url)
                .where(func.lower(Album.artist) == name.lower())
                .where(Album.cover_url.isnot(None))
                .limit(1)
            )
            cover_url = cover_result.scalar_one_or_none()
            if cover_url:
                break
        
        items.append(ArtistResponse(
            name=artist_data["name"],
            track_count=artist_data["track_count"],
            cover_url=cover_url,
        ))
    
    return ArtistsListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
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
    for track, lib_entry in all_tracks:
        if normalize_artist(track.artist) == normalized_search:
            matching_tracks.append((track, lib_entry))
            artist_names_seen.add(track.artist)
    
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
    
    # Top tracks (limited to 10)
    from api.routers.library import track_to_response
    top_tracks = [track_to_response(track, lib_entry) for track, lib_entry in matching_tracks[:10]]
    
    # Albums as response
    from api.routers.albums import album_to_response
    album_items = [album_to_response(album) for album in albums]
    
    return ArtistDetailResponse(
        name=actual_name,
        track_count=track_count,
        album_count=len(albums),
        cover_url=cover_url,
        albums=album_items,
        top_tracks=top_tracks,
    )

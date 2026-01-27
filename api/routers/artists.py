"""
TG Player API v2 - Artists Router

Artist-related endpoints.
Artists are not stored separately - derived from tracks.
"""
from typing import Optional, List

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

from api.routers.auth import get_current_user
from api.schemas_v2.artists import (
    ArtistResponse,
    ArtistDetailResponse,
    ArtistsListResponse,
)
from api.schemas_v2.common import TelegramUser


router = APIRouter(tags=["Artists"])


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
    Get artists from user's library.
    
    Artists are derived from tracks - unique artist names.
    """
    # Base query - get unique artists with track counts
    base_query = (
        select(
            Track.artist,
            func.count(Track.id).label("track_count")
        )
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
        .where(Track.artist.isnot(None))
        .where(Track.artist != "")
        .group_by(Track.artist)
    )
    
    # Apply search
    if search:
        search_term = f"%{search.lower()}%"
        base_query = base_query.where(func.lower(Track.artist).like(search_term))
    
    # Count total
    count_subq = base_query.subquery()
    total = await db.scalar(select(func.count()).select_from(count_subq)) or 0
    
    # Sorting
    if sort_by == "track_count":
        if sort_order == "desc":
            base_query = base_query.order_by(desc("track_count"))
        else:
            base_query = base_query.order_by(asc("track_count"))
    else:
        if sort_order == "desc":
            base_query = base_query.order_by(desc(Track.artist))
        else:
            base_query = base_query.order_by(asc(Track.artist))
    
    # Pagination
    offset = (page - 1) * per_page
    base_query = base_query.offset(offset).limit(per_page)
    
    result = await db.execute(base_query)
    rows = result.all()
    
    # Get cover for each artist (from their first album or enrichment)
    items = []
    for artist_name, track_count in rows:
        # Try to get cover from albums
        cover_result = await db.execute(
            select(Album.cover_url)
            .where(func.lower(Album.artist) == func.lower(artist_name))
            .where(Album.cover_url.isnot(None))
            .limit(1)
        )
        cover_url = cover_result.scalar_one_or_none()
        
        items.append(ArtistResponse(
            name=artist_name,
            track_count=track_count,
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
    """Get artist details with tracks and albums"""
    artist_lower = artist_name.lower()
    
    # Check if user has tracks by this artist
    track_count = await db.scalar(
        select(func.count(Track.id))
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(
            UserLibrary.user_id == user.id,
            func.lower(Track.artist) == artist_lower
        )
    ) or 0
    
    if track_count == 0:
        raise HTTPException(status_code=404, detail="Artist not found in your library")
    
    # Get actual artist name (with proper case)
    name_result = await db.execute(
        select(Track.artist)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(
            UserLibrary.user_id == user.id,
            func.lower(Track.artist) == artist_lower
        )
        .limit(1)
    )
    actual_name = name_result.scalar_one_or_none() or artist_name
    
    # Get albums by this artist in user's library
    user_album_ids = (
        select(AlbumTrack.album_id)
        .distinct()
        .join(UserLibrary, UserLibrary.track_id == AlbumTrack.track_id)
        .where(UserLibrary.user_id == user.id)
        .subquery()
    )
    
    album_result = await db.execute(
        select(Album)
        .where(
            Album.id.in_(select(user_album_ids)),
            func.lower(Album.artist) == artist_lower
        )
        .order_by(Album.release_date.desc().nullslast())
    )
    albums = album_result.scalars().all()
    
    # Get cover URL from albums or enrichment
    cover_url = None
    for album in albums:
        if album.cover_url:
            cover_url = album.cover_url
            break
    
    # Get top tracks (most played)
    from api.routers.library import track_to_response
    
    tracks_result = await db.execute(
        select(Track, UserLibrary)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(
            UserLibrary.user_id == user.id,
            func.lower(Track.artist) == artist_lower
        )
        .options(
            selectinload(Track.enrichment),
            selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
        )
        .order_by(UserLibrary.play_count.desc(), Track.title.asc())
        .limit(10)
    )
    track_rows = tracks_result.unique().all()
    top_tracks = [track_to_response(track, lib_entry) for track, lib_entry in track_rows]
    
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

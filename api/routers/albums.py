"""
TG Player API v2 - Albums Router

Album-related endpoints.
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
from shared.matching import normalize_artist

from api.routers.auth import get_current_user
from api.schemas_v2.albums import (
    AlbumResponse,
    AlbumDetailResponse,
    AlbumsListResponse,
)
from api.schemas_v2.common import TelegramUser


router = APIRouter(tags=["Albums"])


def album_to_response(album: Album, track_count: Optional[int] = None) -> AlbumResponse:
    """Convert Album model to response"""
    # Get actual track count if not provided
    actual_count = track_count if track_count is not None else len(album.tracks) if album.tracks else 0
    
    return AlbumResponse(
        id=album.id,
        name=album.name,
        artist=album.artist,
        cover_url=album.cover_url,
        release_date=album.release_date,
        track_count=actual_count,
        deezer_album_id=album.deezer_album_id,
    )


@router.get("", response_model=AlbumsListResponse)
async def get_my_albums(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    artist: Optional[str] = None,
    sort_by: str = Query("name", pattern="^(name|artist|release_date)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get albums from user's library.
    
    Only returns albums that contain tracks from user's library.
    """
    # Subquery: album IDs that have tracks in user's library
    user_album_ids = (
        select(AlbumTrack.album_id)
        .distinct()
        .join(Track, AlbumTrack.track_id == Track.id)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
        .subquery()
    )
    
    # Base query
    query = select(Album).where(Album.id.in_(select(user_album_ids)))
    count_query = select(func.count(Album.id)).where(Album.id.in_(select(user_album_ids)))
    
    # Apply search
    if search:
        search_term = f"%{search.lower()}%"
        search_filter = (
            func.lower(Album.name).like(search_term) |
            func.lower(Album.artist).like(search_term)
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    
    # Apply artist filter
    if artist:
        artist_lower = artist.lower()
        query = query.where(func.lower(Album.artist) == artist_lower)
        count_query = count_query.where(func.lower(Album.artist) == artist_lower)
    
    # Count total
    total = await db.scalar(count_query) or 0
    
    # Sorting
    if sort_by == "artist":
        sort_column = Album.artist
    elif sort_by == "release_date":
        sort_column = Album.release_date
    else:
        sort_column = Album.name
    
    if sort_order == "desc":
        query = query.order_by(desc(sort_column).nullslast())
    else:
        query = query.order_by(asc(sort_column).nullsfirst())
    
    # Pagination
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    albums = result.scalars().all()
    
    # Get track counts for user's tracks in each album
    if albums:
        album_ids = [a.id for a in albums]
        count_result = await db.execute(
            select(AlbumTrack.album_id, func.count(AlbumTrack.track_id))
            .join(UserLibrary, UserLibrary.track_id == AlbumTrack.track_id)
            .where(
                AlbumTrack.album_id.in_(album_ids),
                UserLibrary.user_id == user.id
            )
            .group_by(AlbumTrack.album_id)
        )
        track_counts = dict(count_result.all())
    else:
        track_counts = {}
    
    items = [
        album_to_response(album, track_counts.get(album.id, 0))
        for album in albums
    ]
    
    return AlbumsListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{album_id}", response_model=AlbumDetailResponse)
async def get_album(
    album_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get album details with tracks from user's library"""
    album = await db.get(Album, album_id)
    
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    # Get tracks from this album that are in user's library
    result = await db.execute(
        select(Track, AlbumTrack, UserLibrary)
        .join(AlbumTrack, AlbumTrack.track_id == Track.id)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(
            AlbumTrack.album_id == album_id,
            UserLibrary.user_id == user.id
        )
        .options(
            selectinload(Track.enrichment),
            selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
        )
        .order_by(AlbumTrack.track_number.asc().nullslast())
    )
    rows = result.all()
    
    from api.routers.library import track_to_response
    tracks = [track_to_response(track, lib_entry) for track, _, lib_entry in rows]
    
    return AlbumDetailResponse(
        id=album.id,
        name=album.name,
        artist=album.artist,
        cover_url=album.cover_url,
        release_date=album.release_date,
        track_count=len(tracks),
        deezer_album_id=album.deezer_album_id,
        tracks=tracks,
    )


@router.get("/by-artist/{artist_name}", response_model=List[AlbumResponse])
async def get_albums_by_artist(
    artist_name: str,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all albums by a specific artist in user's library"""
    artist_lower = artist_name.lower()
    
    # Albums by this artist that have tracks in user's library
    user_album_ids = (
        select(AlbumTrack.album_id)
        .distinct()
        .join(UserLibrary, UserLibrary.track_id == AlbumTrack.track_id)
        .where(UserLibrary.user_id == user.id)
        .subquery()
    )
    
    result = await db.execute(
        select(Album)
        .where(
            Album.id.in_(select(user_album_ids)),
            func.lower(Album.artist) == artist_lower
        )
        .order_by(Album.release_date.desc().nullslast())
    )
    albums = result.scalars().all()
    
    return [album_to_response(album) for album in albums]


@router.get("/{album_id}/ids")
async def get_album_track_ids(
    album_id: int,
    shuffle: bool = False,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all track IDs for an album.
    
    Lightweight endpoint for shuffle - returns only IDs.
    """
    album = await db.get(Album, album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    query = (
        select(Track.id)
        .join(AlbumTrack, AlbumTrack.track_id == Track.id)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(
            AlbumTrack.album_id == album_id,
            UserLibrary.user_id == user.id
        )
    )
    
    if shuffle:
        query = query.order_by(func.random())
    else:
        query = query.order_by(AlbumTrack.track_number.asc().nullslast())
    
    result = await db.execute(query)
    track_ids = result.scalars().all()
    
    return {"ids": track_ids, "total": len(track_ids)}

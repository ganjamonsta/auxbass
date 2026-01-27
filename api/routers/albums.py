"""
TG Player API v2 - Albums Router

Album-related endpoints.
Filters out singles (albums with <2 tracks) and shows full tracklist with missing tracks.
"""
import json
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
from shared.matching import normalize_artist, normalize_title, fuzzy_match_title

from api.routers.auth import get_current_user
from api.schemas_v2.albums import (
    AlbumResponse,
    AlbumDetailResponse,
    AlbumsListResponse,
    AlbumTracklistItem,
)
from api.schemas_v2.common import TelegramUser


router = APIRouter(tags=["Albums"])

# Minimum tracks in user's library to show album (filters out singles)
MIN_USER_TRACKS_FOR_ALBUM = 2


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
        total_tracks=album.total_tracks,
        deezer_album_id=album.deezer_album_id,
        has_full_tracklist=bool(album.full_tracklist),
    )


@router.get("", response_model=AlbumsListResponse)
async def get_my_albums(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    artist: Optional[str] = None,
    sort_by: str = Query("name", pattern="^(name|artist|release_date)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    min_tracks: int = Query(MIN_USER_TRACKS_FOR_ALBUM, ge=1, description="Minimum tracks in library to show album"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get albums from user's library.
    
    Only returns albums that contain at least min_tracks tracks from user's library.
    Default min_tracks=2 filters out singles.
    """
    # Subquery: album IDs with track count >= min_tracks
    album_track_counts = (
        select(
            AlbumTrack.album_id,
            func.count(AlbumTrack.track_id).label("track_count")
        )
        .join(UserLibrary, UserLibrary.track_id == AlbumTrack.track_id)
        .where(UserLibrary.user_id == user.id)
        .group_by(AlbumTrack.album_id)
        .having(func.count(AlbumTrack.track_id) >= min_tracks)
        .subquery()
    )
    
    # Base query - join with filtered album IDs
    query = (
        select(Album, album_track_counts.c.track_count)
        .join(album_track_counts, Album.id == album_track_counts.c.album_id)
    )
    count_query = (
        select(func.count(Album.id))
        .join(album_track_counts, Album.id == album_track_counts.c.album_id)
    )
    
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
    rows = result.all()
    
    # Build response - track counts are included in query result
    items = [
        album_to_response(album, track_count)
        for album, track_count in rows
    ]
    
    return AlbumsListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
    )


# ============== Global Library ==============

@router.get("/global", response_model=AlbumsListResponse)
async def get_global_albums(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    artist: Optional[str] = None,
    sort_by: str = Query("name", pattern="^(name|artist|release_date)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    min_tracks: int = Query(1, ge=1, description="Minimum tracks to show album"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get albums from global public library.
    
    Shows albums that have at least min_tracks public tracks.
    """
    # Subquery: album IDs with public track count >= min_tracks
    album_track_counts = (
        select(
            AlbumTrack.album_id,
            func.count(AlbumTrack.track_id).label("track_count")
        )
        .join(Track, Track.id == AlbumTrack.track_id)
        .where(Track.is_public == True)
        .where(Track.is_unavailable == False)
        .group_by(AlbumTrack.album_id)
        .having(func.count(AlbumTrack.track_id) >= min_tracks)
        .subquery()
    )
    
    # Base query - join with filtered album IDs
    query = (
        select(Album, album_track_counts.c.track_count)
        .join(album_track_counts, Album.id == album_track_counts.c.album_id)
    )
    count_query = (
        select(func.count(Album.id))
        .join(album_track_counts, Album.id == album_track_counts.c.album_id)
    )
    
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
    rows = result.all()
    
    # Build response
    items = [
        album_to_response(album, track_count)
        for album, track_count in rows
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
    """
    Get album details with tracks from user's library.
    
    Returns full_tracklist with in_library flags for each track,
    allowing UI to show missing tracks that can be added.
    """
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
    user_tracks = [(track, lib_entry, at.track_number) for track, at, lib_entry in rows]
    tracks = [track_to_response(track, lib_entry) for track, lib_entry, _ in user_tracks]
    
    # Build full tracklist with in_library status
    full_tracklist = None
    if album.full_tracklist:
        try:
            tracklist_data = json.loads(album.full_tracklist)
            
            # Create lookup by normalized title for matching
            user_tracks_by_title = {}
            for track, lib_entry, track_num in user_tracks:
                norm_title = normalize_title(track.title or "")
                user_tracks_by_title[norm_title] = (track, lib_entry)
            
            full_tracklist = []
            for item in tracklist_data:
                item_title = item.get("title", "")
                norm_item_title = normalize_title(item_title)
                
                # Check if this track is in user's library (fuzzy match)
                matched_track = None
                matched_lib = None
                
                # First try exact normalized match
                if norm_item_title in user_tracks_by_title:
                    matched_track, matched_lib = user_tracks_by_title[norm_item_title]
                else:
                    # Try fuzzy match
                    for norm_title, (track, lib_entry) in user_tracks_by_title.items():
                        if fuzzy_match_title(item_title, track.title or ""):
                            matched_track, matched_lib = track, lib_entry
                            break
                
                tracklist_item = AlbumTracklistItem(
                    track_number=item.get("track_number", 0),
                    title=item_title,
                    artist=item.get("artist", ""),
                    duration=item.get("duration", 0),
                    deezer_id=item.get("deezer_id"),
                    in_library=matched_track is not None,
                    track_id=matched_track.id if matched_track else None,
                    track=track_to_response(matched_track, matched_lib) if matched_track else None,
                )
                full_tracklist.append(tracklist_item)
                
        except (json.JSONDecodeError, Exception) as e:
            # Invalid JSON or error - skip tracklist
            full_tracklist = None
    
    return AlbumDetailResponse(
        id=album.id,
        name=album.name,
        artist=album.artist,
        cover_url=album.cover_url,
        release_date=album.release_date,
        track_count=len(tracks),
        total_tracks=album.total_tracks,
        deezer_album_id=album.deezer_album_id,
        has_full_tracklist=bool(album.full_tracklist),
        tracks=tracks,
        full_tracklist=full_tracklist,
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


@router.post("/{album_id}/find-track")
async def find_missing_track(
    album_id: int,
    title: str = Query(..., description="Track title to search for"),
    artist: Optional[str] = Query(None, description="Artist name (optional)"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Search for a missing track in the global library.
    
    When user clicks "+" on a missing album track:
    1. First search in global tracks table
    2. If found, return track info so user can add to library
    3. If not found, return instructions to send file to bot
    
    Returns:
        found: bool - whether track was found
        track: optional track data if found in global library
        message: instructions for user
    """
    album = await db.get(Album, album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    # Use album's artist if not provided
    search_artist = artist or album.artist
    
    # Normalize for search
    norm_title = normalize_title(title)
    norm_artist = normalize_artist(search_artist) if search_artist else None
    
    # Search in global tracks
    query = select(Track).options(
        selectinload(Track.enrichment),
        selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
    )
    
    # Try to find by normalized title match
    result = await db.execute(query)
    all_tracks = result.scalars().all()
    
    # Find best match
    best_match = None
    best_score = 0.0
    
    for track in all_tracks:
        title_score = fuzzy_match_title(title, track.title or "")
        if title_score < 0.7:
            continue
        
        # Check artist match if we have one
        artist_score = 1.0
        if norm_artist and track.artist:
            from shared.matching import fuzzy_match_artist
            artist_score = fuzzy_match_artist(search_artist, track.artist)
        
        combined = (title_score * 0.6) + (artist_score * 0.4)
        if combined > best_score:
            best_score = combined
            best_match = track
    
    if best_match and best_score >= 0.6:
        # Check if already in user's library
        in_library = await db.scalar(
            select(UserLibrary.id)
            .where(
                UserLibrary.user_id == user.id,
                UserLibrary.track_id == best_match.id
            )
        )
        
        from api.routers.library import track_to_response
        
        return {
            "found": True,
            "in_library": in_library is not None,
            "track_id": best_match.id,
            "track": track_to_response(best_match, None),
            "message": "Трек найден в библиотеке!" if in_library else "Трек найден! Добавить в библиотеку?"
        }
    
    # Not found - suggest sending to bot
    return {
        "found": False,
        "in_library": False,
        "track_id": None,
        "track": None,
        "message": f"Трек не найден. Отправь файл «{title}» боту, чтобы добавить его."
    }


@router.post("/{album_id}/add-track/{track_id}")
async def add_track_to_album_and_library(
    album_id: int,
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add an existing track to user's library and associate with album.
    
    Used when user finds a missing track in global library and wants to add it.
    """
    album = await db.get(Album, album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    track = await db.get(Track, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Check if already in user's library
    existing_lib = await db.scalar(
        select(UserLibrary.id)
        .where(
            UserLibrary.user_id == user.id,
            UserLibrary.track_id == track_id
        )
    )
    
    if not existing_lib:
        # Add to user's library
        from shared.models import LibrarySource
        lib_entry = UserLibrary(
            user_id=user.id,
            track_id=track_id,
            source=LibrarySource.ADDED,  # User explicitly added
        )
        db.add(lib_entry)
    
    # Check if track is already in album
    existing_album_track = await db.scalar(
        select(AlbumTrack.id)
        .where(
            AlbumTrack.album_id == album_id,
            AlbumTrack.track_id == track_id
        )
    )
    
    if not existing_album_track:
        # Determine track number from enrichment or tracklist
        track_number = 0
        if track.enrichment and track.enrichment.track_number:
            track_number = track.enrichment.track_number
        
        album_track = AlbumTrack(
            album_id=album_id,
            track_id=track_id,
            track_number=track_number,
        )
        db.add(album_track)
    
    await db.commit()
    
    return {
        "success": True,
        "message": "Трек добавлен в библиотеку и альбом!",
        "added_to_library": not existing_lib,
        "added_to_album": not existing_album_track,
    }

"""
TG Player API v2 - Library Router

User's personal music library endpoints.
Uses UserLibrary to track user-track relationships.
"""
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import get_db
from shared.models import (
    Track, TrackEnrichment, Album, AlbumTrack, User, UserLibrary,
    EnrichmentStatus, LibrarySource
)
from shared.matching import normalize_artist, normalize_title

from api.routers.auth import get_current_user
from api.schemas_v2.tracks import (
    TrackResponse,
    TracksListResponse,
    TrackUpdate,
)
from api.schemas_v2.library import (
    LibraryStatsResponse,
)
from api.schemas_v2.common import TelegramUser


router = APIRouter(tags=["Library"])


def track_to_response(track: Track, library_entry: Optional[UserLibrary] = None) -> TrackResponse:
    """Convert Track model to response"""
    # Safe access to relationships - check if loaded to avoid lazy loading errors
    enrichment = track.__dict__.get('enrichment')
    
    # Get first album if any (only if already loaded)
    album_info = None
    album_tracks = track.__dict__.get('album_tracks')
    if album_tracks:
        first_album_track = album_tracks[0]
        album = first_album_track.__dict__.get('album') if first_album_track else None
        if album:
            album_info = {
                "id": album.id,
                "name": album.name,
                "cover_url": album.cover_url,
            }
    
    # Determine library source
    source = None
    added_at = track.created_at
    if library_entry:
        source = library_entry.source.value if library_entry.source else None
        added_at = library_entry.added_at
    
    return TrackResponse(
        id=track.id,
        telegram_file_id=track.file_id,
        title=track.title,
        artist=track.artist,
        duration=track.duration,
        file_size=track.file_size,
        library_source=source,
        enrichment_status=track.enrichment_status.value if track.enrichment_status else None,
        album=album_info,
        cover_url=enrichment.cover_url if enrichment else None,
        genre=enrichment.genre if enrichment else None,
        release_date=enrichment.release_date if enrichment else None,
        added_at=added_at,
    )


@router.get("", response_model=TracksListResponse)
async def get_my_tracks(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    artist: Optional[str] = None,
    album_id: Optional[int] = None,
    source: Optional[str] = None,
    sort_by: str = Query("added_at", pattern="^(added_at|title|artist|duration)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get tracks from user's personal library.
    
    Supports filtering by search, artist, album, and source.
    """
    # Base query - join through UserLibrary to get user's tracks
    query = (
        select(Track, UserLibrary)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
        .options(
            selectinload(Track.enrichment),
            selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
        )
    )
    count_query = (
        select(func.count(Track.id))
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
    )
    
    # Search filter
    if search:
        search_term = f"%{search.lower()}%"
        search_filter = or_(
            func.lower(Track.title).like(search_term),
            func.lower(Track.artist).like(search_term),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    
    # Artist filter
    if artist:
        artist_lower = artist.lower()
        query = query.where(func.lower(Track.artist) == artist_lower)
        count_query = count_query.where(func.lower(Track.artist) == artist_lower)
    
    # Album filter
    if album_id:
        query = (
            query
            .join(AlbumTrack, AlbumTrack.track_id == Track.id)
            .where(AlbumTrack.album_id == album_id)
        )
        count_query = (
            count_query
            .join(AlbumTrack, AlbumTrack.track_id == Track.id)
            .where(AlbumTrack.album_id == album_id)
        )
    
    # Source filter
    if source:
        try:
            lib_source = LibrarySource(source)
            query = query.where(UserLibrary.source == lib_source)
            count_query = count_query.where(UserLibrary.source == lib_source)
        except ValueError:
            pass
    
    # Get total count
    total = await db.scalar(count_query) or 0
    
    # Apply sorting
    if album_id:
        # When filtering by album, sort by track number
        query = query.order_by(
            AlbumTrack.track_number.asc().nullslast(),
            Track.title.asc()
        )
    else:
        if sort_by == "added_at":
            sort_column = UserLibrary.added_at
        else:
            sort_column = getattr(Track, sort_by, UserLibrary.added_at)
        
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
    
    # Pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    result = await db.execute(query)
    rows = result.unique().all()
    
    items = [track_to_response(track, lib_entry) for track, lib_entry in rows]
    
    return TracksListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/stats", response_model=LibraryStatsResponse)
async def get_library_stats(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's library statistics"""
    # Total tracks in user's library
    total_tracks = await db.scalar(
        select(func.count(UserLibrary.id))
        .where(UserLibrary.user_id == user.id)
    ) or 0
    
    # Total duration
    total_duration = await db.scalar(
        select(func.sum(Track.duration))
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
    ) or 0
    
    # By source
    source_result = await db.execute(
        select(UserLibrary.source, func.count(UserLibrary.id))
        .where(UserLibrary.user_id == user.id)
        .group_by(UserLibrary.source)
    )
    by_source = {
        source.value if source else "unknown": count
        for source, count in source_result.all()
    }
    
    # Enrichment stats
    enrichment_result = await db.execute(
        select(Track.enrichment_status, func.count(Track.id))
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
        .group_by(Track.enrichment_status)
    )
    enrichment_stats = {
        status.value if status else "unknown": count
        for status, count in enrichment_result.all()
    }
    
    # Album count (albums that have tracks in user's library)
    album_count = await db.scalar(
        select(func.count(func.distinct(AlbumTrack.album_id)))
        .join(Track, AlbumTrack.track_id == Track.id)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
    ) or 0
    
    # Artist count
    artist_count = await db.scalar(
        select(func.count(func.distinct(func.lower(Track.artist))))
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
        .where(Track.artist.isnot(None))
    ) or 0
    
    return LibraryStatsResponse(
        total_tracks=total_tracks,
        total_duration_seconds=total_duration,
        album_count=album_count,
        artist_count=artist_count,
        by_source=by_source,
        enrichment=enrichment_stats,
    )


@router.get("/{track_id}", response_model=TrackResponse)
async def get_track(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific track by ID"""
    result = await db.execute(
        select(Track, UserLibrary)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(Track.id == track_id, UserLibrary.user_id == user.id)
        .options(
            selectinload(Track.enrichment),
            selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
        )
    )
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Track not found in your library")
    
    track, lib_entry = row
    return track_to_response(track, lib_entry)


@router.put("/{track_id}", response_model=TrackResponse)
async def update_track(
    track_id: int,
    update: TrackUpdate,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update track metadata.
    
    If title or artist changes, track will be re-enriched.
    Only the uploader can edit track metadata.
    """
    # Check user has track in library and is uploader
    result = await db.execute(
        select(Track, UserLibrary)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(Track.id == track_id, UserLibrary.user_id == user.id)
    )
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Track not found in your library")
    
    track, lib_entry = row
    
    # Only uploader can edit
    if track.uploader_id != user.id:
        raise HTTPException(status_code=403, detail="Only the uploader can edit track metadata")
    
    changed = False
    
    if update.title and update.title != track.title:
        track.title = update.title
        changed = True
    
    if update.artist and update.artist != track.artist:
        track.artist = update.artist
        changed = True
    
    if changed:
        # Schedule re-enrichment
        track.enrichment_status = EnrichmentStatus.PENDING
        track.updated_at = datetime.utcnow()
    
    await db.commit()
    
    # Reload with relationships
    result = await db.execute(
        select(Track, UserLibrary)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(Track.id == track_id, UserLibrary.user_id == user.id)
        .options(
            selectinload(Track.enrichment),
            selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
        )
    )
    row = result.first()
    track, lib_entry = row
    
    return track_to_response(track, lib_entry)


@router.delete("/{track_id}")
async def remove_from_library(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove a track from user's library.
    
    If user is the uploader and no one else has the track,
    the track itself is deleted.
    """
    # Find library entry
    result = await db.execute(
        select(UserLibrary)
        .where(UserLibrary.track_id == track_id, UserLibrary.user_id == user.id)
    )
    lib_entry = result.scalar_one_or_none()
    
    if not lib_entry:
        raise HTTPException(status_code=404, detail="Track not found in your library")
    
    # Remove from library
    await db.delete(lib_entry)
    
    # Check if anyone else has this track
    other_users = await db.scalar(
        select(func.count(UserLibrary.id))
        .where(UserLibrary.track_id == track_id)
    )
    
    if other_users == 0:
        # No one else has it, check if we should delete
        track = await db.get(Track, track_id)
        if track and track.uploader_id == user.id:
            # Delete the track entirely
            await db.delete(track)
    
    await db.commit()
    
    return {"status": "removed", "track_id": track_id}


@router.post("/{track_id}/enrich")
async def trigger_enrichment(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger enrichment for a track"""
    # Check user has this track
    result = await db.execute(
        select(UserLibrary)
        .where(UserLibrary.track_id == track_id, UserLibrary.user_id == user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Track not found in your library")
    
    track = await db.get(Track, track_id)
    if track:
        track.enrichment_status = EnrichmentStatus.PENDING
        await db.commit()
    
    return {"status": "scheduled", "track_id": track_id}


@router.post("/{track_id}/like")
async def like_track(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle like status for a track"""
    result = await db.execute(
        select(UserLibrary)
        .where(UserLibrary.track_id == track_id, UserLibrary.user_id == user.id)
    )
    lib_entry = result.scalar_one_or_none()
    
    if not lib_entry:
        raise HTTPException(status_code=404, detail="Track not found in your library")
    
    # Toggle like
    lib_entry.is_liked = not lib_entry.is_liked
    if lib_entry.is_liked:
        lib_entry.liked_at = datetime.utcnow()
    else:
        lib_entry.liked_at = None
    
    await db.commit()
    
    return {"status": "liked" if lib_entry.is_liked else "unliked", "track_id": track_id}


@router.get("/liked")
async def get_liked_tracks(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's liked tracks"""
    query = (
        select(Track, UserLibrary)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id, UserLibrary.is_liked == True)
        .options(
            selectinload(Track.enrichment),
            selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
        )
        .order_by(desc(UserLibrary.liked_at))
    )
    
    count_query = (
        select(func.count(UserLibrary.id))
        .where(UserLibrary.user_id == user.id, UserLibrary.is_liked == True)
    )
    
    total = await db.scalar(count_query) or 0
    
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    result = await db.execute(query)
    rows = result.unique().all()
    
    items = [track_to_response(track, lib_entry) for track, lib_entry in rows]
    
    return TracksListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )

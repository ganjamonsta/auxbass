"""
TG Player API v2 - Library Router

User's personal music library endpoints.
Uses UserLibrary to track user-track relationships.
"""
import logging
from typing import Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.database import get_db
from shared.models import (
    Track, TrackEnrichment, Album, AlbumTrack, User, UserLibrary,
    EnrichmentStatus, LibrarySource, utcnow
)
from shared.matching import normalize_artist

from api.routers.auth import get_current_user, require_premium

# NOTE: Cross-layer dependency — channel_service requires aiogram Bot.
from bot.services.channels import get_channel_service
from api.schemas.tracks import (
    TrackResponse,
    TracksListResponse,
    TrackUpdate,
)
from api.schemas.library import (
    LibraryStatsResponse,
)
from api.schemas.common import TelegramUser


router = APIRouter(tags=["Library"])


# ============== Streaming Format Helpers ==============

# MIME types that can be streamed in web player (standard audio player compatible)
STREAMABLE_MIME_TYPES = {
    "audio/mpeg",      # MP3
    "audio/mp3",       # MP3 (alternative)
    "audio/ogg",       # OGG
    "audio/aac",       # AAC
    "audio/mp4",       # M4A
    "audio/x-m4a",     # M4A (alternative)
}

# HD/Lossless MIME types that cannot be streamed (file too large or format unsupported)
HD_MIME_TYPES = {
    "audio/flac",      # FLAC
    "audio/x-flac",    # FLAC (alternative)
    "audio/wav",       # WAV
    "audio/x-wav",     # WAV (alternative)
    "audio/aiff",      # AIFF
    "audio/x-aiff",    # AIFF (alternative)
}


def is_streamable(mime_type: Optional[str]) -> bool:
    """Check if track format can be streamed in web player"""
    if not mime_type:
        return True  # Assume streamable if unknown (legacy data)
    
    mime_lower = mime_type.lower()
    
    # Explicitly HD - not streamable
    if mime_lower in HD_MIME_TYPES:
        return False
    
    # Known streamable or unknown (assume streamable)
    return True


def is_hd_format(mime_type: Optional[str]) -> bool:
    """Check if track is HD/lossless format"""
    if not mime_type:
        return False
    return mime_type.lower() in HD_MIME_TYPES


def track_to_response(track: Track, library_entry: Optional[UserLibrary] = None, *, in_library: Optional[bool] = None) -> TrackResponse:
    """Convert Track model to response. Works for both library and global contexts.
    
    Args:
        track: The Track model
        library_entry: Optional UserLibrary entry (for user's library tracks)
        in_library: Override for in_library flag. Auto-detected from library_entry if None.
    """
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
                "artist": album.artist,
                "cover_url": album.cover_url,
            }
    
    # Extract library context (defaults for global tracks)
    source = None
    added_at = track.created_at
    is_liked = False
    liked_at = None
    play_count = 0
    if library_entry:
        source = library_entry.source.value if library_entry.source else None
        added_at = library_entry.added_at
        is_liked = library_entry.is_liked or False
        liked_at = library_entry.liked_at
        play_count = library_entry.play_count or 0
    
    track_is_streamable = is_streamable(track.mime_type)
    
    # Auto-detect in_library from library_entry if not explicitly set
    if in_library is None:
        in_library = library_entry is not None
    
    return TrackResponse(
        id=track.id,
        telegram_file_id=track.file_id,
        title=track.title,
        artist=track.artist,
        file_name=track.file_name,
        duration=track.duration,
        file_size=track.file_size,
        mime_type=track.mime_type,
        library_source=source,
        is_streamable=track_is_streamable,
        streamable_id=None,
        hd_id=None,
        album=album_info,
        album_name=album_info["name"] if album_info else None,
        cover_url=enrichment.cover_url if enrichment else None,
        genre=enrichment.genre if enrichment else None,
        tags=enrichment.tags if enrichment else None,
        release_date=enrichment.release_date if enrichment else None,
        is_liked=is_liked,
        liked_at=liked_at,
        play_count=play_count,
        added_at=added_at,
        in_library=in_library,
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
        # Use ilike for case-insensitive search (works better with Cyrillic in PostgreSQL)
        search_term = f"%{search}%"
        search_filter = or_(
            Track.title.ilike(search_term),
            Track.artist.ilike(search_term),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    
    # Artist filter
    if artist:
        query = query.where(Track.artist.ilike(artist))
        count_query = count_query.where(Track.artist.ilike(artist))
    
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


@router.get("/ids")
async def get_all_track_ids(
    search: Optional[str] = None,
    artist: Optional[str] = None,
    album_id: Optional[int] = None,
    source: Optional[str] = None,
    liked_only: bool = False,
    sort_by: str = Query("added_at", pattern="^(added_at|title|artist|duration|random)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all track IDs from user's library.
    
    Lightweight endpoint for shuffle - returns only IDs, not full track data.
    Use this to build a complete shuffle queue, then load tracks on-demand.
    
    Args:
        search: Filter by search query
        artist: Filter by artist name
        album_id: Filter by album ID
        source: Filter by library source (forwarded, search, etc.)
        liked_only: Only return liked tracks
        sort_by: Sort field. Use 'random' for pre-shuffled order
        sort_order: asc or desc
    
    Returns:
        List of track IDs in requested order
    """
    query = (
        select(Track.id)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
    )
    
    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Track.title.ilike(search_term),
                Track.artist.ilike(search_term),
            )
        )
    
    # Artist filter
    if artist:
        query = query.where(Track.artist.ilike(artist))
    
    # Album filter
    if album_id:
        query = query.join(AlbumTrack, AlbumTrack.track_id == Track.id).where(AlbumTrack.album_id == album_id)
    
    # Source filter
    if source:
        try:
            source_enum = LibrarySource(source)
            query = query.where(UserLibrary.source == source_enum)
        except ValueError:
            pass
    
    # Liked filter
    if liked_only:
        query = query.where(UserLibrary.is_liked == True)
    
    # Sorting
    if sort_by == "random":
        query = query.order_by(func.random())
    else:
        if sort_by == "added_at":
            sort_column = UserLibrary.added_at
        elif sort_by == "title":
            sort_column = Track.title
        elif sort_by == "artist":
            sort_column = Track.artist
        elif sort_by == "duration":
            sort_column = Track.duration
        else:
            sort_column = UserLibrary.added_at
        
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
    
    result = await db.execute(query)
    track_ids = result.scalars().all()
    
    return {"ids": list(track_ids), "total": len(track_ids)}


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
    
    # Album count (albums that have tracks in user's library)
    album_count = await db.scalar(
        select(func.count(func.distinct(AlbumTrack.album_id)))
        .join(Track, AlbumTrack.track_id == Track.id)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
    ) or 0
    
    # Artist count - using normalized artist names
    artist_count = await db.scalar(
        select(func.count(func.distinct(func.lower(func.trim(Track.artist)))))
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
        .where(Track.artist.isnot(None))
        .where(Track.artist != '')
    ) or 0
    
    return LibraryStatsResponse(
        total_tracks=total_tracks,
        total_duration_seconds=total_duration,
        album_count=album_count,
        artist_count=artist_count,
        by_source=by_source,
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
    
    If title, artist, or genre changes, track will be re-enriched.
    Only the uploader can edit track metadata.
    """
    # Check user has track in library and is uploader
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
    
    # Only uploader can edit
    if track.uploader_id != user.id:
        raise HTTPException(status_code=403, detail="Only the uploader can edit track metadata")
    
    changed = False
    
    if update.title and update.title.strip() and update.title.strip() != track.title:
        track.title = update.title.strip()
        changed = True
    
    if update.artist and update.artist.strip() and update.artist.strip() != track.artist:
        track.artist = update.artist.strip()
        changed = True
    
    # Update genre if provided
    if hasattr(update, 'genre') and update.genre is not None and update.genre.strip():
        if not track.enrichment:
            track.enrichment = TrackEnrichment(track_id=track.id)
        if track.enrichment.genre != update.genre.strip():
            track.enrichment.genre = update.genre.strip()
            changed = True
    
    if changed:
        # Schedule re-enrichment
        track.enrichment_status = EnrichmentStatus.PENDING
        track.updated_at = utcnow()
    
    await db.commit()
    
    # Reload with relationships to return fresh data
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
        raise HTTPException(status_code=500, detail="Track disappeared after update")
    
    track, lib_entry = row
    
    return track_to_response(track, lib_entry)


@router.delete("/{track_id}")
async def remove_from_library(
    track_id: int,
    user: TelegramUser = Depends(require_premium),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove a track from user's library. Requires connected channel.
    
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
    user: TelegramUser = Depends(require_premium),
    db: AsyncSession = Depends(get_db),
):
    """Toggle like status for a track - auto-adds to library if not already there. Requires connected channel."""
    result = await db.execute(
        select(UserLibrary)
        .where(UserLibrary.track_id == track_id, UserLibrary.user_id == user.id)
    )
    lib_entry = result.scalar_one_or_none()
    
    added_to_library = False
    
    if not lib_entry:
        # Track not in library - check if track exists and is public, then auto-add with like
        track = await db.scalar(
            select(Track).where(Track.id == track_id, Track.is_public == True)
        )
        if not track:
            raise HTTPException(status_code=404, detail="Track not found")
        
        # Auto-add to library with like
        lib_entry = UserLibrary(
            user_id=user.id,
            track_id=track_id,
            source=LibrarySource.ADDED,
            is_liked=True,
            liked_at=utcnow(),
        )
        db.add(lib_entry)
        added_to_library = True
        await db.commit()
        
        # Pin track message in user's channel
        try:
            channel_svc = get_channel_service()
            await channel_svc.pin_track_in_channel(user.id, track_id)
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to pin track {track_id} in channel: {e}")
        
        return {"status": "liked", "track_id": track_id, "added_to_library": True}
    
    # Toggle like
    lib_entry.is_liked = not lib_entry.is_liked
    if lib_entry.is_liked:
        lib_entry.liked_at = utcnow()
    else:
        lib_entry.liked_at = None
    
    await db.commit()
    
    # Pin or unpin track message in user's channel based on new like state
    try:
        channel_svc = get_channel_service()
        if lib_entry.is_liked:
            await channel_svc.pin_track_in_channel(user.id, track_id)
        else:
            await channel_svc.unpin_track_in_channel(user.id, track_id)
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to pin/unpin track {track_id} in channel: {e}")
    
    return {"status": "liked" if lib_entry.is_liked else "unliked", "track_id": track_id, "added_to_library": False}


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

"""
TG Player API v2 - Library Router

User's personal music library endpoints.
Uses UserLibrary to track user-track relationships.
"""
import logging
from typing import Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_, desc, asc, String, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.database import get_db
from shared.models import (
    Track, TrackEnrichment, TrackTag, Album, AlbumTrack, User, UserLibrary,
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
    LibrarySyncStateResponse,
    LibrarySyncStats,
)
from api.schemas.common import TelegramUser


router = APIRouter(tags=["Library"])


# ============== Shared utilities (canonical source: api.utils.responses) ==============
# Re-exported here for backwards compatibility with existing importers.
# New code should import directly from api.utils.responses.
from api.utils.responses import (
    STREAMABLE_MIME_TYPES,
    HD_MIME_TYPES,
    MAX_STREAMABLE_SIZE_BYTES,
    is_streamable,
    is_hd_format,
    streamable_track_filter,
    track_to_response,
    build_track_search_filter,
)


@router.get("", response_model=TracksListResponse)
async def get_my_tracks(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    offset: Optional[int] = Query(None, ge=0),
    limit: Optional[int] = Query(None, ge=1, le=100),
    search: Optional[str] = None,
    artist: Optional[str] = None,
    album_id: Optional[int] = None,
    source: Optional[str] = None,
    include_disliked: bool = Query(False, description="Include disliked tracks"),
    sort_by: str = Query("added_at", pattern="^(added_at|title|artist|duration)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get tracks from user's personal library.
    
    Supports filtering by search, artist, album, and source.
    Supports both page/per_page and offset/limit pagination.
    """
    # Base query - join through UserLibrary to get user's tracks
    base_conds = [UserLibrary.user_id == user.id]
    if not include_disliked:
        base_conds.append(UserLibrary.is_disliked == False)
    
    query = (
        select(Track, UserLibrary)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(*base_conds)
        .options(
            selectinload(Track.enrichment),
            selectinload(Track.track_tags),
            selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
        )
    )
    count_query = (
        select(func.count(Track.id))
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(*base_conds)
    )
    
    # Search filter (indexes title, artist, file_name, user tags, and enrichment tags)
    if search:
        search_filter = build_track_search_filter(search)
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
    
    # Ensure string sorting parameters even when called directly in tests
    effective_sort_by = sort_by if isinstance(sort_by, str) else getattr(sort_by, 'default', 'added_at') or 'added_at'
    effective_sort_order = sort_order if isinstance(sort_order, str) else getattr(sort_order, 'default', 'desc') or 'desc'

    # Apply sorting
    if album_id:
        # When filtering by album, sort by track number
        query = query.order_by(
            AlbumTrack.track_number.asc().nullslast(),
            Track.title.asc()
        )
    else:
        if effective_sort_by == "added_at":
            sort_column = UserLibrary.added_at
        else:
            sort_column = getattr(Track, effective_sort_by, UserLibrary.added_at)
        
        if effective_sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
    
    # Pagination: support both offset/limit and page/per_page
    effective_limit = limit or per_page
    if offset is not None:
        effective_offset = offset
        effective_page = (offset // effective_limit) + 1
    else:
        effective_offset = (page - 1) * effective_limit
        effective_page = page
    
    query = query.offset(effective_offset).limit(effective_limit)
    
    result = await db.execute(query)
    rows = result.unique().all()
    
    items = [track_to_response(track, lib_entry) for track, lib_entry in rows]
    
    return TracksListResponse(
        items=items,
        total=total,
        offset=effective_offset,
        limit=effective_limit,
        page=effective_page,
        per_page=effective_limit,
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
        .where(UserLibrary.is_disliked == False)
        .where(streamable_track_filter())
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
    # 1. Combined main stats: total tracks, total duration, and artist count in one single query
    main_stats_query = (
        select(
            func.count(UserLibrary.id).label("total_tracks"),
            func.coalesce(func.sum(Track.duration), 0).label("total_duration"),
            func.count(
                func.distinct(
                    func.nullif(
                        func.coalesce(Track.normalized_artist, func.lower(func.trim(Track.artist))),
                        ''
                    )
                )
            ).label("artist_count"),
        )
        .select_from(UserLibrary)
        .join(Track, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
    )
    main_result = await db.execute(main_stats_query)
    main_row = main_result.one()

    total_tracks = main_row.total_tracks or 0
    total_duration = main_row.total_duration or 0
    artist_count = main_row.artist_count or 0

    if total_tracks == 0:
        return LibraryStatsResponse(
            total_tracks=0,
            total_duration_seconds=0,
            album_count=0,
            artist_count=0,
            by_source={},
        )

    # 2. Album count (albums that have tracks in user's library) - direct 2-table join
    album_count = await db.scalar(
        select(func.count(func.distinct(AlbumTrack.album_id)))
        .select_from(UserLibrary)
        .join(AlbumTrack, AlbumTrack.track_id == UserLibrary.track_id)
        .where(UserLibrary.user_id == user.id)
    ) or 0

    # 3. By source
    source_result = await db.execute(
        select(UserLibrary.source, func.count(UserLibrary.id))
        .where(UserLibrary.user_id == user.id)
        .group_by(UserLibrary.source)
    )
    by_source = {
        source.value if hasattr(source, "value") and source else (source or "unknown"): count
        for source, count in source_result.all()
    }

    return LibraryStatsResponse(
        total_tracks=total_tracks,
        total_duration_seconds=total_duration,
        album_count=album_count,
        artist_count=artist_count,
        by_source=by_source,
    )


@router.get("/sync-state", response_model=LibrarySyncStateResponse)
async def get_library_sync_state(
    since: Optional[datetime] = Query(None, description="ISO timestamp of last sync"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lightweight sync state check for webapp.
    Allows frontend to detect new tracks and metadata updates in near real-time.
    """
    stats_query = (
        select(
            func.count(UserLibrary.id).label("total_tracks"),
            func.max(UserLibrary.track_id).label("last_track_id"),
            func.max(UserLibrary.added_at).label("last_added_at"),
            func.max(Track.updated_at).label("last_updated_at"),
            func.count(
                func.distinct(
                    func.nullif(
                        func.coalesce(Track.normalized_artist, func.lower(func.trim(Track.artist))),
                        ''
                    )
                )
            ).label("artist_count"),
        )
        .select_from(UserLibrary)
        .join(Track, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
        .where(UserLibrary.is_disliked == False)
    )
    res = await db.execute(stats_query)
    row = res.one()

    total_tracks = row.total_tracks or 0
    last_track_id = row.last_track_id
    last_added_at = row.last_added_at
    last_updated_at = row.last_updated_at
    artist_count = row.artist_count or 0

    if total_tracks == 0:
        return LibrarySyncStateResponse(
            total_tracks=0,
            last_track_id=None,
            last_added_at=None,
            last_updated_at=None,
            updated_tracks=[],
            stats=LibrarySyncStats(total_tracks=0, artist_count=0, album_count=0),
        )

    # Album count (albums that have tracks in user's library)
    album_count = await db.scalar(
        select(func.count(func.distinct(AlbumTrack.album_id)))
        .select_from(UserLibrary)
        .join(AlbumTrack, AlbumTrack.track_id == UserLibrary.track_id)
        .where(UserLibrary.user_id == user.id)
    ) or 0

    sync_stats = LibrarySyncStats(
        total_tracks=total_tracks,
        artist_count=artist_count,
        album_count=album_count,
    )

    updated_tracks: List[TrackResponse] = []
    if since and isinstance(since, datetime):
        since_naive = since.replace(tzinfo=None) if since.tzinfo else since
        updated_query = (
            select(Track, UserLibrary)
            .join(UserLibrary, UserLibrary.track_id == Track.id)
            .where(UserLibrary.user_id == user.id)
            .where(UserLibrary.is_disliked == False)
            .where(Track.updated_at > since_naive)
            .options(
                selectinload(Track.enrichment),
                selectinload(Track.track_tags),
                selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
            )
            .order_by(desc(Track.updated_at))
            .limit(30)
        )
        up_res = await db.execute(updated_query)
        updated_tracks = [track_to_response(t, lib) for t, lib in up_res.unique().all()]

    return LibrarySyncStateResponse(
        total_tracks=total_tracks,
        last_track_id=last_track_id,
        last_added_at=last_added_at,
        last_updated_at=last_updated_at,
        updated_tracks=updated_tracks,
        stats=sync_stats,
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
    
    Allowed for track uploader or any user who has the track in their library.
    """
    # Fetch track with relations
    result = await db.execute(
        select(Track)
        .where(Track.id == track_id)
        .options(
            selectinload(Track.enrichment),
            selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
        )
    )
    track = result.scalar_one_or_none()
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Check permission: user must be uploader OR have track in UserLibrary
    lib_result = await db.execute(
        select(UserLibrary)
        .where(UserLibrary.user_id == user.id, UserLibrary.track_id == track_id)
    )
    lib_entry = lib_result.scalar_one_or_none()
    
    if track.uploader_id != user.id and not lib_entry:
        raise HTTPException(status_code=403, detail="Track not found in your library")
    
    changed = False
    
    if update.title is not None and update.title.strip():
        new_title = update.title.strip()
        if new_title != track.title:
            track.title = new_title
            changed = True
    
    if update.artist is not None and update.artist.strip():
        new_artist = update.artist.strip()
        if new_artist != track.artist:
            track.artist = new_artist
            track.normalized_artist = normalize_artist(new_artist)
            changed = True
    
    # Update genre if provided
    if update.genre is not None:
        new_genre = update.genre.strip() or None
        if not track.enrichment:
            track.enrichment = TrackEnrichment(track_id=track.id)
            db.add(track.enrichment)
        if track.enrichment.genre != new_genre:
            track.enrichment.genre = new_genre
            changed = True

    # Update album if provided
    if update.album is not None:
        new_album = update.album.strip()
        if not track.enrichment:
            track.enrichment = TrackEnrichment(track_id=track.id)
            db.add(track.enrichment)
        
        if track.enrichment.album_name != (new_album or None):
            track.enrichment.album_name = new_album or None
            changed = True
        
        if new_album:
            try:
                from bot.services.albums import album_service
                album_id = await album_service.find_or_create_album(
                    album_name=new_album,
                    artist_name=track.artist or "Unknown Artist",
                )
                await album_service.assign_track_to_album(track.id, album_id)
                changed = True
            except Exception as e:
                logger.warning(f"Failed to assign album '{new_album}' to track {track.id}: {e}")
        else:
            await db.execute(
                delete(AlbumTrack).where(AlbumTrack.track_id == track.id)
            )
            changed = True
    
    if changed:
        track.updated_at = utcnow()
        # Mark as completed so background worker doesn't overwrite manual edits on restart
        track.enrichment_status = EnrichmentStatus.COMPLETED
    
    await db.commit()
    
    if changed:
        try:
            from bot.services.channels import get_channel_service
            ch_svc = get_channel_service()
            await ch_svc.update_channel_message(track_id)
        except Exception as e:
            logger.debug(f"Failed to update channel message for track {track_id}: {e}")
    
    # Reload with relationships to return fresh data
    result = await db.execute(
        select(Track)
        .where(Track.id == track_id)
        .options(
            selectinload(Track.enrichment),
            selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
        )
    )
    track = result.scalar_one_or_none()
    
    if not track:
        raise HTTPException(status_code=500, detail="Track disappeared after update")
    
    # Reload lib_entry
    lib_result = await db.execute(
        select(UserLibrary)
        .where(UserLibrary.user_id == user.id, UserLibrary.track_id == track_id)
    )
    lib_entry = lib_result.scalar_one_or_none()
    
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
        try:
            from bot.services.enrichment import enrichment_worker
            enrichment_worker.notify_new_track()
        except Exception:
            pass
    
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

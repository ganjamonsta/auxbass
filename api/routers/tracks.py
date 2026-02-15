"""
TG Player API v2 - Tracks Router (Backwards Compatibility)

Provides /tracks endpoints for backwards compatibility with webapp.
Delegates to library, artists, albums routers where appropriate.
"""
import logging
from typing import Optional, List
from datetime import datetime, timezone
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc, asc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.database import get_db
from shared.models import (
    Track, TrackEnrichment, Album, AlbumTrack, User, UserLibrary,
    EnrichmentStatus, LibrarySource, utcnow
)
from shared.matching import normalize_artist

# NOTE: Cross-layer dependency — channel_service requires aiogram Bot.
# The API lifespan initializes the bot and channel_service.
# TODO: Extract channel forwarding logic into shared/ layer.
from bot.services.channels import get_channel_service

from api.routers.auth import get_current_user, require_premium, get_optional_user
from api.routers.library import track_to_response
from api.schemas.tracks import (
    TrackResponse,
    TracksListResponse,
    TrackUpdate,
)
from api.schemas.common import TelegramUser


logger = logging.getLogger(__name__)

router = APIRouter(tags=["Tracks"])


# ============== Track IDs (Lightweight for Shuffle) ==============

@router.get("/ids")
async def get_track_ids(
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
    ids = [row[0] for row in result.all()]
    
    return {"ids": ids, "total": len(ids)}


# ============== Enrichment Status ==============

@router.get("/enrichment/status")
async def get_enrichment_status(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get enrichment status for user's library"""
    result = await db.execute(
        select(Track.enrichment_status, func.count(Track.id))
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
        .group_by(Track.enrichment_status)
    )
    
    stats = {
        "pending": 0,
        "processing": 0,
        "completed": 0,
        "failed": 0,
    }
    
    for status, count in result.all():
        if status:
            stats[status.value] = count
    
    total = sum(stats.values())
    
    return {
        "total": total,
        "pending": stats["pending"],
        "processing": stats["processing"],
        "completed": stats["completed"],
        "failed": stats["failed"],
        "progress": round((stats["completed"] / total * 100) if total > 0 else 0, 1)
    }


# ============== Artists from Tracks ==============

@router.get("/artists")
async def get_artists(
    scope: str = Query("library", pattern="^(library|global)$"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get unique artists from tracks with normalization"""
    # Get all artist names
    if scope == "library":
        query = (
            select(Track.artist)
            .join(UserLibrary, UserLibrary.track_id == Track.id)
            .where(UserLibrary.user_id == user.id)
            .where(Track.artist.isnot(None))
            .where(Track.artist != "")
        )
    else:
        query = (
            select(Track.artist)
            .join(User, User.id == Track.uploader_id)
            .where(Track.is_public == True)
            .where(User.hide_profile == False)
            .where(Track.artist.isnot(None))
            .where(Track.artist != "")
        )
    
    result = await db.execute(query)
    artists_raw = [row[0] for row in result.all()]
    
    # Group by normalized artist name
    # Key: normalized_name -> {display_name, count, display_priority}
    artist_groups = defaultdict(lambda: {"display_name": None, "count": 0, "priority": 0})
    
    for artist in artists_raw:
        normalized = normalize_artist(artist)
        if not normalized:
            continue
            
        group = artist_groups[normalized]
        group["count"] += 1
        
        # Choose best display name:
        # 1. Prefer title case (starts with uppercase)
        # 2. Prefer shorter names (without feat, etc.)
        # 3. First encountered as fallback
        is_title_case = artist[0].isupper() if artist else False
        has_collab = any(sep in artist.lower() for sep in [' & ', ' + ', ' x ', ', ', ' feat', ' ft.'])
        
        priority = 0
        if is_title_case:
            priority += 2
        if not has_collab:
            priority += 1
            
        if group["display_name"] is None or priority > group["priority"]:
            group["display_name"] = artist
            group["priority"] = priority
    
    # Convert to list and sort by count
    artists_list = [
        {
            "artist": data["display_name"],
            "name": data["display_name"],
            "track_count": data["count"],
            "normalized": normalized
        }
        for normalized, data in artist_groups.items()
    ]
    
    # Sort by track count descending
    artists_list.sort(key=lambda x: x["track_count"], reverse=True)
    
    return artists_list


@router.get("/artist-image/{artist_name}")
async def get_artist_image(
    artist_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Get artist image (from album cover, matched by normalized artist name)"""
    normalized_search = normalize_artist(artist_name)
    
    # Get all albums with covers
    result = await db.execute(
        select(Album)
        .where(Album.cover_url.isnot(None))
        .where(Album.artist.isnot(None))
    )
    albums = result.scalars().all()
    
    # Find matching album by normalized artist
    for album in albums:
        if normalize_artist(album.artist) == normalized_search:
            return {"image_url": album.cover_url}
    
    # Try from track enrichment
    result = await db.execute(
        select(TrackEnrichment.cover_url, Track.artist)
        .join(Track, Track.id == TrackEnrichment.track_id)
        .where(TrackEnrichment.cover_url.isnot(None))
        .where(Track.artist.isnot(None))
    )
    
    for cover_url, track_artist in result.all():
        if normalize_artist(track_artist) == normalized_search:
            return {"image_url": cover_url}
    
    return {"image_url": None}


@router.get("/artist/{artist_name}")
async def get_artist_detail(
    artist_name: str,
    scope: str = Query("library", pattern="^(library|global)$"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get artist details with their tracks (matches by normalized artist name)"""
    # Normalize the search artist name
    normalized_search = normalize_artist(artist_name)
    
    if scope == "library":
        query = (
            select(Track, UserLibrary)
            .join(UserLibrary, UserLibrary.track_id == Track.id)
            .where(UserLibrary.user_id == user.id)
            .where(Track.artist.isnot(None))
            .options(
                selectinload(Track.enrichment),
                selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
            )
            .order_by(desc(UserLibrary.added_at))
        )
    else:
        query = (
            select(Track)
            .join(User, User.id == Track.uploader_id)
            .where(Track.is_public == True)
            .where(User.hide_profile == False)
            .where(Track.artist.isnot(None))
            .options(
                selectinload(Track.enrichment),
                selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
            )
            .order_by(desc(Track.play_count), desc(Track.created_at))
        )
    
    result = await db.execute(query)
    
    # Filter tracks by normalized artist name in Python
    if scope == "library":
        rows = result.unique().all()
        tracks = []
        for track, lib in rows:
            if normalize_artist(track.artist) == normalized_search:
                tracks.append(track_to_response(track, lib))
    else:
        rows = result.unique().scalars().all()
        tracks = []
        for track in rows:
            if normalize_artist(track.artist) == normalized_search:
                tracks.append(track_to_response(track))
    
    # Get albums for this artist (also by normalized name)
    albums_result = await db.execute(
        select(Album)
        .where(Album.artist.isnot(None))
        .order_by(desc(Album.release_date))
    )
    all_albums = albums_result.scalars().all()
    albums = [a for a in all_albums if normalize_artist(a.artist) == normalized_search]
    
    return {
        "name": artist_name,
        "track_count": len(tracks),
        "album_count": len(albums),
        "tracks": tracks,
        "albums": [
            {
                "id": a.id,
                "name": a.name,
                "cover_url": a.cover_url,
                "release_date": a.release_date,
            }
            for a in albums
        ]
    }


@router.get("/artist/{artist_name}/ids")
async def get_artist_track_ids(
    artist_name: str,
    sort_by: str = Query("added_at", pattern="^(added_at|title|duration|random)$"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all track IDs for an artist.
    
    Lightweight endpoint for shuffle by artist.
    """
    normalized_search = normalize_artist(artist_name)
    
    query = (
        select(Track.id, Track.artist, UserLibrary.added_at)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
        .where(Track.artist.isnot(None))
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    # Filter by normalized artist name
    matching_ids = [
        (row[0], row[2])  # (track_id, added_at)
        for row in rows
        if normalize_artist(row[1]) == normalized_search
    ]
    
    # Sort
    if sort_by == "random":
        import random
        random.shuffle(matching_ids)
        ids = [item[0] for item in matching_ids]
    else:
        # Sort by added_at desc
        matching_ids.sort(key=lambda x: x[1] or datetime.min, reverse=True)
        ids = [item[0] for item in matching_ids]
    
    return {"ids": ids, "total": len(ids)}


# ============== Genres ==============

@router.get("/genres")
async def get_genres(
    scope: str = Query("library", pattern="^(library|global)$"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get unique genres from tracks"""
    if scope == "library":
        query = (
            select(TrackEnrichment.genre, func.count(TrackEnrichment.id).label("count"))
            .join(Track, Track.id == TrackEnrichment.track_id)
            .join(UserLibrary, UserLibrary.track_id == Track.id)
            .where(UserLibrary.user_id == user.id)
            .where(TrackEnrichment.genre.isnot(None))
            .where(TrackEnrichment.genre != "")
            .group_by(TrackEnrichment.genre)
            .order_by(desc("count"))
        )
    else:
        query = (
            select(TrackEnrichment.genre, func.count(TrackEnrichment.id).label("count"))
            .join(Track, Track.id == TrackEnrichment.track_id)
            .where(Track.is_public == True)
            .where(TrackEnrichment.genre.isnot(None))
            .where(TrackEnrichment.genre != "")
            .group_by(TrackEnrichment.genre)
            .order_by(desc("count"))
        )
    
    result = await db.execute(query)
    
    return [
        {"name": genre, "track_count": count}
        for genre, count in result.all()
    ]


# ============== Tags (Last.fm + User) ==============

@router.get("/tags")
async def get_tags(
    scope: str = Query("library", pattern="^(library|global)$"),
    limit: int = Query(50, ge=1, le=200),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get unique tags from tracks with counts.
    
    Now reads from normalized track_tags table (includes both
    enrichment tags from Last.fm and user-generated tags).
    """
    from shared.models import TrackTag, TrackTagVote
    
    if scope == "library":
        query = (
            select(
                TrackTag.tag,
                func.count(func.distinct(TrackTag.track_id)).label("track_count"),
                func.count(TrackTagVote.id).label("total_votes"),
            )
            .outerjoin(TrackTagVote, TrackTagVote.track_tag_id == TrackTag.id)
            .join(Track, Track.id == TrackTag.track_id)
            .join(UserLibrary, UserLibrary.track_id == Track.id)
            .where(UserLibrary.user_id == user.id)
            .group_by(TrackTag.tag)
            .order_by(desc("track_count"))
            .limit(limit)
        )
    else:
        query = (
            select(
                TrackTag.tag,
                func.count(func.distinct(TrackTag.track_id)).label("track_count"),
                func.count(TrackTagVote.id).label("total_votes"),
            )
            .outerjoin(TrackTagVote, TrackTagVote.track_tag_id == TrackTag.id)
            .join(Track, Track.id == TrackTag.track_id)
            .where(Track.is_public == True)
            .group_by(TrackTag.tag)
            .order_by(desc("track_count"))
            .limit(limit)
        )
    
    result = await db.execute(query)
    
    return [
        {"name": tag, "track_count": track_count, "total_votes": total_votes}
        for tag, track_count, total_votes in result.all()
    ]


# ============== Play History ==============

@router.get("/history")
async def get_play_history(
    limit: int = Query(50, ge=1, le=200),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's recently played tracks"""
    query = (
        select(Track, UserLibrary)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
        .where(UserLibrary.last_played_at.isnot(None))
        .options(
            selectinload(Track.enrichment),
            selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
        )
        .order_by(desc(UserLibrary.last_played_at))
        .limit(limit)
    )
    
    result = await db.execute(query)
    rows = result.unique().all()
    
    return {
        "items": [track_to_response(track, lib) for track, lib in rows],
        "total": len(rows)
    }


# ============== Liked Tracks ==============

@router.get("/liked")
async def get_liked_tracks(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's liked tracks"""
    query = (
        select(Track, UserLibrary)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
        .where(UserLibrary.is_liked == True)
        .options(
            selectinload(Track.enrichment),
            selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
        )
        .order_by(desc(UserLibrary.liked_at))
    )
    
    result = await db.execute(query)
    rows = result.unique().all()
    
    return {
        "items": [track_to_response(track, lib) for track, lib in rows],
        "total": len(rows)
    }


# ============== Unavailable Tracks ==============

@router.get("/unavailable/list")
async def get_unavailable_tracks(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's unavailable tracks"""
    query = (
        select(Track, UserLibrary)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
        .where(Track.is_unavailable == True)
        .options(
            selectinload(Track.enrichment),
            selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
        )
    )
    
    result = await db.execute(query)
    rows = result.unique().all()
    
    return {
        "items": [track_to_response(track, lib) for track, lib in rows],
        "total": len(rows)
    }


@router.delete("/unavailable/all")
async def delete_all_unavailable(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove all unavailable tracks from user's library and channel"""
    # Get unavailable tracks in user's library
    result = await db.execute(
        select(UserLibrary)
        .join(Track, Track.id == UserLibrary.track_id)
        .where(UserLibrary.user_id == user.id)
        .where(Track.is_unavailable == True)
    )
    entries = result.scalars().all()
    
    track_ids = [entry.track_id for entry in entries]
    count = len(entries)
    for entry in entries:
        await db.delete(entry)
    
    await db.commit()
    
    # Channel = mirror of library: delete from channel too
    if track_ids:
        try:
            channel_service = get_channel_service()
            for tid in track_ids:
                await channel_service.delete_track_from_channel(user.id, tid)
        except Exception as e:
            logger.warning(f"Failed to delete unavailable tracks from channel: {e}")
    
    return {"removed": count}


# ============== Global Library ==============

@router.get("/global")
async def get_global_tracks(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[TelegramUser] = Depends(get_optional_user),
):
    """Get public tracks from global library"""
    query = (
        select(Track)
        .where(Track.is_public == True)
        .where(Track.is_unavailable == False)
        .options(
            selectinload(Track.enrichment),
            selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
        )
    )
    
    if search:
        # Use ilike for case-insensitive search (works better with Cyrillic in PostgreSQL)
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Track.title.ilike(search_term),
                Track.artist.ilike(search_term),
            )
        )
    
    count_query = select(func.count(Track.id)).where(
        Track.is_public == True,
        Track.is_unavailable == False
    )
    if search:
        count_query = count_query.where(
            or_(
                Track.title.ilike(search_term),
                Track.artist.ilike(search_term),
            )
        )
    
    total = await db.scalar(count_query) or 0
    
    offset = (page - 1) * per_page
    query = query.order_by(desc(Track.created_at)).offset(offset).limit(per_page)
    
    result = await db.execute(query)
    tracks = result.unique().scalars().all()
    
    # Check which tracks are in user's library
    user_track_ids = set()
    if current_user:
        lib_result = await db.execute(
            select(UserLibrary.track_id).where(UserLibrary.user_id == current_user.id)
        )
        user_track_ids = set(lib_result.scalars().all())
    
    return TracksListResponse(
        items=[track_to_response(t, in_library=(t.id in user_track_ids)) for t in tracks],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/global/recent")
async def get_recent_uploads(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get recently uploaded public tracks"""
    query = (
        select(Track)
        .where(Track.is_public == True)
        .where(Track.is_unavailable == False)
        .options(
            selectinload(Track.enrichment),
            selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
        )
        .order_by(desc(Track.created_at))
        .limit(limit)
    )
    
    result = await db.execute(query)
    tracks = result.unique().scalars().all()
    
    return {
        "items": [track_to_response(t) for t in tracks],
        "total": len(tracks)
    }


@router.get("/global/popular")
async def get_popular_tracks(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get most played public tracks"""
    query = (
        select(Track)
        .where(Track.is_public == True)
        .where(Track.is_unavailable == False)
        .where(Track.play_count > 0)
        .options(
            selectinload(Track.enrichment),
            selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
        )
        .order_by(desc(Track.play_count))
        .limit(limit)
    )
    
    result = await db.execute(query)
    tracks = result.unique().scalars().all()
    
    return {
        "items": [track_to_response(t) for t in tracks],
        "total": len(tracks)
    }


@router.get("/global/stats")
async def get_global_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get global library statistics"""
    total_tracks = await db.scalar(
        select(func.count(Track.id)).where(Track.is_public == True)
    ) or 0
    
    total_users = await db.scalar(select(func.count(User.id))) or 0
    
    total_albums = await db.scalar(select(func.count(Album.id))) or 0
    
    total_plays = await db.scalar(
        select(func.sum(Track.play_count)).where(Track.is_public == True)
    ) or 0
    
    return {
        "total_tracks": total_tracks,
        "total_users": total_users,
        "total_albums": total_albums,
        "total_plays": total_plays,
    }


@router.get("/global/users")
async def get_top_users(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get top uploaders"""
    query = (
        select(User, func.count(Track.id).label("upload_count"))
        .join(Track, Track.uploader_id == User.id)
        .where(Track.is_public == True)
        .group_by(User.id)
        .order_by(desc("upload_count"))
        .limit(limit)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "upload_count": count,
        }
        for user, count in rows
    ]


@router.get("/global/users/{user_id}/tracks")
async def get_user_tracks(
    user_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get public tracks from a specific user"""
    query = (
        select(Track)
        .where(Track.uploader_id == user_id)
        .where(Track.is_public == True)
        .where(Track.is_unavailable == False)
        .options(
            selectinload(Track.enrichment),
            selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
        )
        .order_by(desc(Track.created_at))
        .limit(limit)
    )
    
    result = await db.execute(query)
    tracks = result.unique().scalars().all()
    
    return {
        "items": [track_to_response(t) for t in tracks],
        "total": len(tracks)
    }


# ============== Track Operations ==============

@router.get("/{track_id}")
async def get_track(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get single track"""
    result = await db.execute(
        select(Track, UserLibrary)
        .outerjoin(
            UserLibrary,
            (UserLibrary.track_id == Track.id) & (UserLibrary.user_id == user.id)
        )
        .where(Track.id == track_id)
        .options(
            selectinload(Track.enrichment),
            selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
        )
    )
    row = result.unique().first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Track not found")
    
    track, lib_entry = row
    return track_to_response(track, lib_entry)


@router.put("/{track_id}")
async def update_track(
    track_id: int,
    data: TrackUpdate,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update track metadata (only owner can update)"""
    result = await db.execute(
        select(Track)
        .where(Track.id == track_id)
        .where(Track.uploader_id == user.id)
    )
    track = result.scalar_one_or_none()
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found or not owned")
    
    # Validate and update metadata
    changed = False
    if data.title is not None and data.title.strip():
        track.title = data.title.strip()
        changed = True
    
    if data.artist is not None and data.artist.strip():
        track.artist = data.artist.strip()
        changed = True
    
    # Update genre if provided
    if hasattr(data, 'genre') and data.genre is not None and data.genre.strip():
        # Genre updates come through enrichment
        if not track.enrichment:
            track.enrichment = TrackEnrichment(track_id=track.id)
        track.enrichment.genre = data.genre.strip()
        changed = True
    
    if changed:
        track.updated_at = utcnow()
        track.enrichment_status = EnrichmentStatus.PENDING
    
    await db.commit()

    # Re-fetch track with all relations (just refresh from DB)
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
    
    # Get UserLibrary entry if it exists
    lib_result = await db.execute(
        select(UserLibrary)
        .where(UserLibrary.user_id == user.id, UserLibrary.track_id == track_id)
    )
    lib_entry = lib_result.scalar_one_or_none()
    
    return track_to_response(track, lib_entry)


@router.delete("/{track_id}")
async def delete_track(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete track from library and channel (channel = mirror of library)"""
    result = await db.execute(
        select(UserLibrary)
        .where(UserLibrary.track_id == track_id)
        .where(UserLibrary.user_id == user.id)
    )
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Track not found in your library")
    
    await db.delete(entry)
    await db.commit()
    
    # Channel = mirror of library: delete from channel too
    deleted_from_channel = False
    try:
        channel_service = get_channel_service()
        deleted_from_channel = await channel_service.delete_track_from_channel(user.id, track_id)
    except Exception as e:
        logger.warning(f"Failed to delete track {track_id} from channel: {e}")
    
    return {"status": "deleted", "track_id": track_id, "deleted_from_channel": deleted_from_channel}


@router.post("/{track_id}/like")
async def like_track(
    track_id: int,
    user: TelegramUser = Depends(require_premium),
    db: AsyncSession = Depends(get_db),
):
    """Like a track - auto-adds to library if not already there. Requires connected channel."""
    result = await db.execute(
        select(UserLibrary)
        .where(UserLibrary.track_id == track_id)
        .where(UserLibrary.user_id == user.id)
    )
    entry = result.scalar_one_or_none()
    
    added_to_library = False
    forwarded = False
    
    if not entry:
        # Track not in library - check if track exists and is public, then auto-add
        track = await db.scalar(
            select(Track).where(Track.id == track_id, Track.is_public == True)
        )
        if not track:
            raise HTTPException(status_code=404, detail="Track not found")
        
        # Auto-add to library
        entry = UserLibrary(
            user_id=user.id,
            track_id=track_id,
            source=LibrarySource.ADDED,
            is_liked=True,
            liked_at=utcnow(),
        )
        db.add(entry)
        added_to_library = True
        logger.info(f"Track {track_id} auto-added to library and liked by user {user.id}")
        
        # Forward to user's channel (if auto_forward is enabled)
        await db.commit()  # Commit first so track is in library
        try:
            channel_service = get_channel_service()
            forwarded = await channel_service.forward_track_to_channel(user.id, track_id)
            if forwarded:
                logger.info(f"Track {track_id} forwarded to channel for user {user.id}")
        except Exception as e:
            logger.warning(f"Failed to forward track {track_id} to channel: {e}")
    else:
        entry.is_liked = True
        entry.liked_at = utcnow()
        await db.commit()
    
    # Pin track message in user's channel
    pinned = False
    try:
        channel_svc = get_channel_service()
        pinned = await channel_svc.pin_track_in_channel(user.id, track_id)
    except Exception as e:
        logger.warning(f"Failed to pin track {track_id} in channel: {e}")
    
    return {"status": "liked", "track_id": track_id, "added_to_library": added_to_library, "forwarded": forwarded, "pinned": pinned}


@router.delete("/{track_id}/like")
async def unlike_track(
    track_id: int,
    user: TelegramUser = Depends(require_premium),
    db: AsyncSession = Depends(get_db),
):
    """Unlike a track. Requires connected channel."""
    result = await db.execute(
        select(UserLibrary)
        .where(UserLibrary.track_id == track_id)
        .where(UserLibrary.user_id == user.id)
    )
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Track not found in your library")
    
    entry.is_liked = False
    entry.liked_at = None
    await db.commit()
    
    # Unpin track message in user's channel
    try:
        channel_svc = get_channel_service()
        await channel_svc.unpin_track_in_channel(user.id, track_id)
    except Exception as e:
        logger.warning(f"Failed to unpin track {track_id} in channel: {e}")
    
    return {"status": "unliked", "track_id": track_id}


@router.post("/{track_id}/mark-unavailable")
async def mark_unavailable(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark track as unavailable.
    
    Any authenticated user can report a track as unavailable - this allows
    users browsing global library to report broken tracks they encounter.
    The track's file_id may have become invalid on Telegram's side.
    
    When the original uploader (or anyone) sends the file to the bot again,
    the file_id will be updated and is_unavailable will be cleared.
    """
    result = await db.execute(
        select(Track).where(Track.id == track_id)
    )
    track = result.scalar_one_or_none()
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Only mark if not already unavailable
    if not track.is_unavailable:
        track.is_unavailable = True
        await db.commit()
        logger.info(f"Track {track_id} marked as unavailable by user {user.id}")
    
    return {"status": "marked_unavailable", "track_id": track_id}


@router.post("/{track_id}/add-to-library")
async def add_to_library(
    track_id: int,
    user: TelegramUser = Depends(require_premium),
    db: AsyncSession = Depends(get_db),
):
    """Add a global track to user's library and forward to user's channel."""
    # Check track exists and is public
    result = await db.execute(
        select(Track).where(Track.id == track_id).where(Track.is_public == True)
    )
    track = result.scalar_one_or_none()
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found or not public")
    
    # Check if already in library
    result = await db.execute(
        select(UserLibrary)
        .where(UserLibrary.track_id == track_id)
        .where(UserLibrary.user_id == user.id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Track already in library")
    
    # Add to library
    entry = UserLibrary(
        user_id=user.id,
        track_id=track_id,
        source=LibrarySource.ADDED,
    )
    db.add(entry)
    await db.commit()
    
    # Forward to user's channel (if auto_forward is enabled) - uses queue
    queued = False
    try:
        channel_service = get_channel_service()
        queued = await channel_service.forward_track_to_channel(user.id, track_id)
        if queued:
            logger.info(f"Track {track_id} queued for channel forward for user {user.id}")
    except Exception as e:
        logger.warning(f"Failed to queue track {track_id} for channel: {e}")
    
    return {"status": "added", "track_id": track_id, "queued_for_channel": queued}


@router.delete("/{track_id}/remove-from-library")
async def remove_from_library(
    track_id: int,
    user: TelegramUser = Depends(require_premium),
    db: AsyncSession = Depends(get_db),
):
    """Remove a track from user's library and channel (channel = mirror of library)."""
    result = await db.execute(
        select(UserLibrary)
        .where(UserLibrary.track_id == track_id)
        .where(UserLibrary.user_id == user.id)
    )
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Track not found in your library")
    
    await db.delete(entry)
    await db.commit()
    
    # Channel = mirror of library: always delete from channel
    deleted_from_channel = False
    try:
        channel_service = get_channel_service()
        deleted_from_channel = await channel_service.delete_track_from_channel(user.id, track_id)
    except Exception as e:
        logger.warning(f"Failed to delete track {track_id} from channel: {e}")
    
    return {"status": "removed", "track_id": track_id, "deleted_from_channel": deleted_from_channel}


# ============== Get all tracks (alias for backwards compat) ==============

@router.get("")
async def get_all_tracks(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: str = Query("added_at", pattern="^(added_at|title|artist|duration)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's tracks (alias for /library)"""
    query = (
        select(Track, UserLibrary)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
        .options(
            selectinload(Track.enrichment),
            selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
        )
    )
    
    if search:
        # Use ilike for case-insensitive search (works better with Cyrillic in PostgreSQL)
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Track.title.ilike(search_term),
                Track.artist.ilike(search_term),
            )
        )
    
    # Count
    count_query = (
        select(func.count(UserLibrary.id))
        .where(UserLibrary.user_id == user.id)
    )
    if search:
        count_query = count_query.join(Track, Track.id == UserLibrary.track_id).where(
            or_(
                Track.title.ilike(search_term),
                Track.artist.ilike(search_term),
            )
        )
    
    total = await db.scalar(count_query) or 0
    
    # Sorting
    order_col = {
        "added_at": UserLibrary.added_at,
        "title": Track.title,
        "artist": Track.artist,
        "duration": Track.duration,
    }.get(sort_by, UserLibrary.added_at)
    
    if sort_order == "desc":
        query = query.order_by(desc(order_col))
    else:
        query = query.order_by(asc(order_col))
    
    # Pagination with offset/limit
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    rows = result.unique().all()
    
    return TracksListResponse(
        items=[track_to_response(track, lib) for track, lib in rows],
        total=total,
        offset=offset,
        limit=limit,
    )

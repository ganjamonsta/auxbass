"""
TG Player API v2 - Playlists Router

User playlist management.
"""
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, delete, update, union_all, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.database import get_db
from shared.models import Playlist, PlaylistTrack, Track, UserLibrary, AlbumTrack, User, PlaylistSubscription, TrackEnrichment
from shared.config import get_settings

from api.routers.auth import get_current_user, require_premium
from api.routers.library import track_to_response
from api.schemas.common import TelegramUser, PaginatedResponse
from api.schemas.tracks import TrackResponse
from api.schemas.playlists import (
    PlaylistCreate,
    PlaylistUpdate,
    PlaylistResponse,
    PlaylistDetailResponse,
    PlaylistsListResponse,
    AddTrackRequest,
    ReorderRequest,
)


router = APIRouter(tags=["Playlists"])


async def get_playlist_info(
    db: AsyncSession, 
    playlist_id: int
) -> tuple[int, int, Optional[str], List[str]]:
    """
    Get track count, duration, cover, and covers array for a playlist.
    Returns: (track_count, total_duration, cover_url, covers)
    Cover is built from track covers (collage of up to 4 track covers).
    """
    # Count and duration
    result = await db.execute(
        select(
            func.count(PlaylistTrack.id),
            func.coalesce(func.sum(Track.duration), 0)
        )
        .join(Track, Track.id == PlaylistTrack.track_id)
        .where(PlaylistTrack.playlist_id == playlist_id)
    )
    row = result.one()
    track_count = row[0] or 0
    total_duration = row[1] or 0
    
    # Get track covers for collage (up to 4)
    covers_result = await db.execute(
        select(Track)
        .join(PlaylistTrack, PlaylistTrack.track_id == Track.id)
        .join(TrackEnrichment, TrackEnrichment.track_id == Track.id)
        .where(PlaylistTrack.playlist_id == playlist_id)
        .where(TrackEnrichment.cover_url.is_not(None))
        .where(TrackEnrichment.cover_url != "")
        .options(selectinload(Track.enrichment))
        .order_by(PlaylistTrack.position)
        .limit(4)
    )
    track_covers = []
    for track in covers_result.scalars().all():
        if track.enrichment and track.enrichment.cover_url:
            track_covers.append(track.enrichment.cover_url)
    
    # Build covers array from track covers (up to 4 for collage)
    covers = track_covers[:4]
    cover_url = track_covers[0] if track_covers else None
    
    return track_count, total_duration, cover_url, covers


@router.get("", response_model=PlaylistsListResponse)
async def get_my_playlists(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(name|track_count|created_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    include_subscribed: bool = Query(True, description="Include subscribed playlists"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's public playlists (owned and subscribed). Supports search, sort and offset/limit pagination."""
    # Build set of user's visible playlist IDs (owned and subscribed)
    owned_ids_q = (
        select(Playlist.id)
        .where(Playlist.owner_id == user.id)
    )
    
    if include_subscribed:
        subscribed_ids_q = (
            select(Playlist.id)
            .join(PlaylistSubscription, PlaylistSubscription.playlist_id == Playlist.id)
            .where(PlaylistSubscription.user_id == user.id)
            .where(Playlist.is_public == True)
        )
        all_ids_subq = union_all(owned_ids_q, subscribed_ids_q).subquery()
        base_filter = Playlist.id.in_(select(all_ids_subq.c.id))
    else:
        base_filter = (Playlist.owner_id == user.id)
    
    # Track count subquery (for display and sort)
    track_count_subq = (
        select(
            PlaylistTrack.playlist_id,
            func.count(PlaylistTrack.id).label('track_count')
        )
        .group_by(PlaylistTrack.playlist_id)
        .subquery()
    )
    
    # Base query
    query = (
        select(Playlist, User, func.coalesce(track_count_subq.c.track_count, 0).label('tc'))
        .join(User, User.id == Playlist.owner_id)
        .outerjoin(track_count_subq, track_count_subq.c.playlist_id == Playlist.id)
        .where(base_filter)
    )
    count_query = (
        select(func.count(Playlist.id))
        .where(base_filter)
    )
    
    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.where(Playlist.name.ilike(search_term))
        count_query = count_query.where(Playlist.name.ilike(search_term))
    
    # Count total
    total = await db.scalar(count_query) or 0
    
    # Sorting
    if sort_by == "name":
        sort_column = Playlist.name
    elif sort_by == "track_count":
        sort_column = func.coalesce(track_count_subq.c.track_count, 0)
    else:
        sort_column = Playlist.created_at
    
    if sort_order == "desc":
        query = query.order_by(desc(sort_column).nullslast(), desc(Playlist.id))
    else:
        query = query.order_by(asc(sort_column).nullsfirst(), asc(Playlist.id))
    
    # Pagination
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    items = []
    for playlist, owner, tc in rows:
        _, total_duration, cover_url, covers = await get_playlist_info(db, playlist.id)
        
        is_owner = playlist.owner_id == user.id
        is_subscribed = False
        if not is_owner:
            subscription = await db.scalar(
                select(PlaylistSubscription)
                .where(
                    PlaylistSubscription.user_id == user.id,
                    PlaylistSubscription.playlist_id == playlist.id
                )
            )
            is_subscribed = subscription is not None
        
        items.append(PlaylistResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            track_count=tc,
            total_duration=total_duration,
            cover_url=cover_url,
            covers=covers,
            is_public=playlist.is_public,
            owner_id=owner.id,
            owner_name=owner.display_name,
            is_owner=is_owner,
            is_subscribed=is_subscribed,
            created_at=playlist.created_at,
        ))
    
    return PlaylistsListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/manage/all", response_model=PlaylistsListResponse)
async def get_all_my_playlists(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get ALL user's playlists including private ones (for management/settings)"""
    # Count all owned playlists
    total = await db.scalar(
        select(func.count(Playlist.id))
        .where(Playlist.owner_id == user.id)
    ) or 0
    
    # Get all playlists
    offset = (page - 1) * per_page
    result = await db.execute(
        select(Playlist, User)
        .join(User, User.id == Playlist.owner_id)
        .where(Playlist.owner_id == user.id)
        .order_by(Playlist.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    rows = result.all()
    
    items = []
    for playlist, owner in rows:
        track_count, total_duration, cover_url, covers = await get_playlist_info(db, playlist.id)
        items.append(PlaylistResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            track_count=track_count,
            total_duration=total_duration,
            cover_url=cover_url,
            covers=covers,
            is_public=playlist.is_public,
            owner_id=owner.id,
            owner_name=owner.display_name,
            is_owner=True,
            is_subscribed=False,
            created_at=playlist.created_at,
        ))
    
    return PlaylistsListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )


# ============== Global Playlists ==============

@router.get("/global", response_model=PlaylistsListResponse)
async def get_global_playlists(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(name|track_count|created_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all public playlists from global library.
    
    Shows all public playlists with pagination, search and sort.
    """
    # Track count subquery
    track_count_subq = (
        select(
            PlaylistTrack.playlist_id,
            func.count(PlaylistTrack.id).label('track_count')
        )
        .group_by(PlaylistTrack.playlist_id)
        .subquery()
    )
    
    # Base query
    query = (
        select(Playlist, User, func.coalesce(track_count_subq.c.track_count, 0).label('tc'))
        .join(User, User.id == Playlist.owner_id)
        .outerjoin(track_count_subq, track_count_subq.c.playlist_id == Playlist.id)
        .where(Playlist.is_public == True)
    )
    count_query = (
        select(func.count(Playlist.id))
        .where(Playlist.is_public == True)
    )
    
    # Apply search
    if search:
        search_term = f"%{search}%"
        search_filter = (
            Playlist.name.ilike(search_term) |
            User.display_name.ilike(search_term)
        )
        query = query.where(search_filter)
        count_query = (
            select(func.count(Playlist.id))
            .join(User, User.id == Playlist.owner_id)
            .where(Playlist.is_public == True)
            .where(search_filter)
        )
    
    # Count total
    total = await db.scalar(count_query) or 0
    
    # Sorting
    if sort_by == "name":
        sort_column = Playlist.name
    elif sort_by == "track_count":
        sort_column = func.coalesce(track_count_subq.c.track_count, 0)
    else:
        sort_column = Playlist.created_at
    
    if sort_order == "desc":
        query = query.order_by(desc(sort_column).nullslast(), desc(Playlist.id))
    else:
        query = query.order_by(asc(sort_column).nullsfirst(), asc(Playlist.id))
    
    # Pagination
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    items = []
    for playlist, owner, tc in rows:
        _, total_duration, cover_url, covers = await get_playlist_info(db, playlist.id)
        
        is_owner = playlist.owner_id == user.id
        is_subscribed = False
        if not is_owner:
            subscription = await db.scalar(
                select(PlaylistSubscription)
                .where(
                    PlaylistSubscription.user_id == user.id,
                    PlaylistSubscription.playlist_id == playlist.id
                )
            )
            is_subscribed = subscription is not None
        
        items.append(PlaylistResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            track_count=tc,
            total_duration=total_duration,
            cover_url=cover_url,
            covers=covers,
            is_public=playlist.is_public,
            owner_id=owner.id,
            owner_name=owner.display_name,
            is_owner=is_owner,
            is_subscribed=is_subscribed,
            created_at=playlist.created_at,
        ))
    
    return PlaylistsListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post("", response_model=PlaylistResponse)
async def create_playlist(
    data: PlaylistCreate,
    user: TelegramUser = Depends(require_premium),
    db: AsyncSession = Depends(get_db),
):
    """Create a new playlist. Requires connected channel."""
    playlist = Playlist(
        owner_id=user.id,
        name=data.name,
        description=data.description,
        is_public=data.is_public,
    )
    db.add(playlist)
    await db.flush()
    await db.commit()
    
    # Get user info for response
    owner = await db.get(User, user.id)
    
    return PlaylistResponse(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        track_count=0,
        total_duration=0,
        cover_url=None,
        covers=[],
        is_public=playlist.is_public,
        owner_id=owner.id,
        owner_name=owner.display_name,
        is_owner=True,
        is_subscribed=False,
        created_at=playlist.created_at,
    )


@router.get("/{playlist_id}", response_model=PlaylistDetailResponse)
async def get_playlist(
    playlist_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get playlist with tracks"""
    result = await db.execute(
        select(Playlist, User)
        .join(User, User.id == Playlist.owner_id)
        .where(Playlist.id == playlist_id)
    )
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    playlist, owner = row
    
    # Allow access if owner or if playlist is public
    if playlist.owner_id != user.id and not playlist.is_public:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Get tracks with library entries for response
    result = await db.execute(
        select(Track, UserLibrary)
        .join(PlaylistTrack, PlaylistTrack.track_id == Track.id)
        .outerjoin(UserLibrary, (UserLibrary.track_id == Track.id) & (UserLibrary.user_id == user.id))
        .where(PlaylistTrack.playlist_id == playlist_id)
        .options(
            selectinload(Track.enrichment),
            selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
        )
        .order_by(PlaylistTrack.position)
    )
    rows = result.unique().all()
    
    tracks_response = [track_to_response(track, lib_entry) for track, lib_entry in rows]
    
    track_count = len(tracks_response)
    total_duration = sum(t.duration or 0 for t in [row[0] for row in rows])
    
    # Build covers array from track covers (up to 4 for collage)
    track_covers = []
    for track, _ in rows:
        if track.enrichment and track.enrichment.cover_url and len(track_covers) < 4:
            track_covers.append(track.enrichment.cover_url)
    cover_url = track_covers[0] if track_covers else None
    covers = track_covers
    
    # Check if user is subscribed to this playlist
    is_subscribed = False
    if playlist.owner_id != user.id:
        subscription = await db.scalar(
            select(PlaylistSubscription)
            .where(
                PlaylistSubscription.user_id == user.id,
                PlaylistSubscription.playlist_id == playlist_id
            )
        )
        is_subscribed = subscription is not None
    
    # Collect tags from playlist tracks (aggregate unique tags)
    playlist_tags = None
    try:
        seen_tags = set()
        collected_tags = []
        for track, _ in rows:
            if track.enrichment and track.enrichment.tags:
                for tag in track.enrichment.tags:
                    tag_lower = tag.lower()
                    if tag_lower not in seen_tags:
                        seen_tags.add(tag_lower)
                        collected_tags.append(tag)
                        if len(collected_tags) >= 5:
                            break
            if len(collected_tags) >= 5:
                break
        if collected_tags:
            playlist_tags = collected_tags
    except Exception:
        playlist_tags = None
    
    return PlaylistDetailResponse(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        track_count=track_count,
        total_duration=total_duration,
        cover_url=cover_url,
        covers=covers,
        tags=playlist_tags,
        is_public=playlist.is_public,
        owner_id=owner.id,
        owner_name=owner.display_name,
        is_owner=playlist.owner_id == user.id,
        is_subscribed=is_subscribed,
        created_at=playlist.created_at,
        tracks=tracks_response,
    )


@router.get("/{playlist_id}/ids")
async def get_playlist_track_ids(
    playlist_id: int,
    shuffle: bool = False,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all track IDs for a playlist.
    
    Lightweight endpoint for shuffle - returns only IDs.
    Allows access to public playlists even if user is not the owner.
    """
    playlist = await db.get(Playlist, playlist_id)
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Allow access if owner or if playlist is public
    if playlist.owner_id != user.id and not playlist.is_public:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    query = (
        select(Track.id)
        .join(PlaylistTrack, PlaylistTrack.track_id == Track.id)
        .where(PlaylistTrack.playlist_id == playlist_id)
    )
    
    if shuffle:
        query = query.order_by(func.random())
    else:
        query = query.order_by(PlaylistTrack.position.asc())
    
    result = await db.execute(query)
    track_ids = result.scalars().all()
    
    return {"ids": track_ids, "total": len(track_ids)}


@router.put("/{playlist_id}", response_model=PlaylistResponse)
async def update_playlist(
    playlist_id: int,
    data: PlaylistUpdate,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update playlist name, description, and visibility."""
    playlist = await db.get(Playlist, playlist_id)
    
    if not playlist or playlist.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    if data.name:
        playlist.name = data.name
    if data.description is not None:
        playlist.description = data.description
    if data.is_public is not None:
        playlist.is_public = data.is_public
    
    await db.commit()
    
    track_count, total_duration, cover_url, covers = await get_playlist_info(db, playlist.id)
    
    return PlaylistResponse(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        track_count=track_count,
        total_duration=total_duration,
        cover_url=cover_url,
        covers=covers,
        is_public=playlist.is_public,
        created_at=playlist.created_at,
    )



@router.delete("/{playlist_id}")
async def delete_playlist(
    playlist_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete playlist."""
    playlist = await db.get(Playlist, playlist_id)
    
    if not playlist or playlist.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Delete track associations first
    await db.execute(
        delete(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist_id)
    )
    
    await db.delete(playlist)
    await db.commit()
    
    return {"status": "deleted", "playlist_id": playlist_id}


@router.post("/{playlist_id}/tracks")
async def add_track_to_playlist(
    playlist_id: int,
    data: AddTrackRequest,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add track to playlist."""
    playlist = await db.get(Playlist, playlist_id)
    
    if not playlist or playlist.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Check track exists - allow both library tracks and global tracks
    track = await db.get(Track, data.track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Check if already in playlist
    existing = await db.scalar(
        select(PlaylistTrack)
        .where(
            PlaylistTrack.playlist_id == playlist_id,
            PlaylistTrack.track_id == data.track_id
        )
    )
    if existing:
        raise HTTPException(status_code=400, detail="Track already in playlist")
    
    # Get next position
    max_pos = await db.scalar(
        select(func.coalesce(func.max(PlaylistTrack.position), 0))
        .where(PlaylistTrack.playlist_id == playlist_id)
    ) or 0
    
    pt = PlaylistTrack(
        playlist_id=playlist_id,
        track_id=data.track_id,
        position=max_pos + 1,
    )
    db.add(pt)
    await db.commit()
    
    return {"status": "added", "position": max_pos + 1}


@router.delete("/{playlist_id}/tracks/{track_id}")
async def remove_track_from_playlist(
    playlist_id: int,
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove track from playlist."""
    playlist = await db.get(Playlist, playlist_id)
    
    if not playlist or playlist.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    pt = await db.scalar(
        select(PlaylistTrack)
        .where(
            PlaylistTrack.playlist_id == playlist_id,
            PlaylistTrack.track_id == track_id
        )
    )
    
    if not pt:
        raise HTTPException(status_code=404, detail="Track not in playlist")
    
    await db.delete(pt)
    await db.commit()
    
    return {"status": "removed"}


@router.put("/{playlist_id}/reorder")
async def reorder_playlist(
    playlist_id: int,
    data: ReorderRequest,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reorder tracks in playlist."""
    playlist = await db.get(Playlist, playlist_id)
    
    if not playlist or playlist.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Update positions
    for position, track_id in enumerate(data.track_ids):
        await db.execute(
            update(PlaylistTrack)
            .where(
                PlaylistTrack.playlist_id == playlist_id,
                PlaylistTrack.track_id == track_id
            )
            .values(position=position)
        )
    
    await db.commit()
    
    return {"status": "reordered"}


# ============== Public Playlists ==============

@router.get("/public/explore", response_model=PlaylistsListResponse)
async def get_public_playlists(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all public playlists from all users"""
    # Count public playlists
    total = await db.scalar(
        select(func.count(Playlist.id))
        .where(Playlist.is_public == True)
    ) or 0
    
    # Get playlists with owner info
    offset = (page - 1) * per_page
    result = await db.execute(
        select(Playlist, User)
        .join(User, User.id == Playlist.owner_id)
        .where(Playlist.is_public == True)
        .order_by(Playlist.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    rows = result.all()
    
    items = []
    for playlist, owner in rows:
        track_count, total_duration, cover_url, covers = await get_playlist_info(db, playlist.id)
        
        # Check if current user is subscribed or is owner
        is_owner = playlist.owner_id == user.id
        is_subscribed = False
        if not is_owner:
            subscription = await db.scalar(
                select(PlaylistSubscription)
                .where(
                    PlaylistSubscription.user_id == user.id,
                    PlaylistSubscription.playlist_id == playlist.id
                )
            )
            is_subscribed = subscription is not None
        
        items.append(PlaylistResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            track_count=track_count,
            total_duration=total_duration,
            cover_url=cover_url,
            covers=covers,
            is_public=playlist.is_public,
            owner_id=owner.id,
            owner_name=owner.display_name,
            is_owner=is_owner,
            is_subscribed=is_subscribed,
            created_at=playlist.created_at,
        ))
    
    return PlaylistsListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/user/{user_id}", response_model=PlaylistsListResponse)
async def get_user_public_playlists(
    user_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get public playlists of a specific user"""
    # If viewing own playlists, show all
    is_own = user_id == user.id
    
    query = select(Playlist).where(Playlist.owner_id == user_id)
    if not is_own:
        query = query.where(Playlist.is_public == True)
    
    # Count
    total = await db.scalar(
        select(func.count(Playlist.id))
        .where(Playlist.owner_id == user_id)
        .where(True if is_own else Playlist.is_public == True)
    ) or 0
    
    # Get owner info
    owner = await db.get(User, user_id)
    if not owner:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get playlists
    offset = (page - 1) * per_page
    result = await db.execute(
        query.order_by(Playlist.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    playlists = result.scalars().all()
    
    items = []
    for playlist in playlists:
        track_count, total_duration, cover_url, covers = await get_playlist_info(db, playlist.id)
        # Check if current user is subscribed
        is_subscribed = False
        if not is_own:
            subscription = await db.scalar(
                select(PlaylistSubscription)
                .where(
                    PlaylistSubscription.user_id == user.id,
                    PlaylistSubscription.playlist_id == playlist.id
                )
            )
            is_subscribed = subscription is not None
        
        items.append(PlaylistResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            track_count=track_count,
            total_duration=total_duration,
            cover_url=cover_url,
            covers=covers,
            is_public=playlist.is_public,
            owner_id=owner.id,
            owner_name=owner.display_name,
            is_owner=is_own,
            is_subscribed=is_subscribed,
            created_at=playlist.created_at,
        ))
    
    return PlaylistsListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )


# ============== Playlist Subscription ==============

@router.post("/{playlist_id}/subscribe")
async def subscribe_to_playlist(
    playlist_id: int,
    user: TelegramUser = Depends(require_premium),
    db: AsyncSession = Depends(get_db),
):
    """
    Subscribe to a public playlist.
    Adds the playlist to user's library with auto-updates.
    """
    # Check playlist exists and is public
    result = await db.execute(
        select(Playlist, User)
        .join(User, User.id == Playlist.owner_id)
        .where(Playlist.id == playlist_id)
    )
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    playlist, owner = row
    
    if not playlist.is_public:
        raise HTTPException(status_code=400, detail="Playlist is not public")
    
    if playlist.owner_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot subscribe to your own playlist")
    
    # Check if already subscribed
    existing = await db.scalar(
        select(PlaylistSubscription)
        .where(
            PlaylistSubscription.user_id == user.id,
            PlaylistSubscription.playlist_id == playlist_id
        )
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already subscribed to this playlist")
    
    # Create subscription
    subscription = PlaylistSubscription(
        user_id=user.id,
        playlist_id=playlist_id,
    )
    db.add(subscription)
    await db.commit()
    
    return {
        "status": "subscribed",
        "playlist_id": playlist_id,
        "playlist_name": playlist.name,
        "owner_name": owner.display_name,
    }


@router.delete("/{playlist_id}/subscribe")
async def unsubscribe_from_playlist(
    playlist_id: int,
    user: TelegramUser = Depends(require_premium),
    db: AsyncSession = Depends(get_db),
):
    """Unsubscribe from a playlist."""
    result = await db.execute(
        delete(PlaylistSubscription)
        .where(
            PlaylistSubscription.user_id == user.id,
            PlaylistSubscription.playlist_id == playlist_id
        )
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Not subscribed to this playlist")
    
    await db.commit()
    
    return {"status": "unsubscribed", "playlist_id": playlist_id}


@router.get("/{playlist_id}/subscribers")
async def get_playlist_subscribers(
    playlist_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of users subscribed to a playlist (owner only)."""
    playlist = await db.get(Playlist, playlist_id)
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    if playlist.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only playlist owner can view subscribers")
    
    # Count
    total = await db.scalar(
        select(func.count(PlaylistSubscription.id))
        .where(PlaylistSubscription.playlist_id == playlist_id)
    ) or 0
    
    # Get subscribers
    offset = (page - 1) * per_page
    result = await db.execute(
        select(User)
        .join(PlaylistSubscription, PlaylistSubscription.user_id == User.id)
        .where(PlaylistSubscription.playlist_id == playlist_id)
        .order_by(PlaylistSubscription.subscribed_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    users = result.scalars().all()
    
    items = [
        {
            "id": u.id,
            "username": u.username,
            "display_name": u.display_name,
        }
        for u in users
    ]
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


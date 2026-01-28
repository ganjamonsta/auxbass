"""
TG Player API v2 - Playlists Router

User playlist management.
"""
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import get_db
from shared.models import Playlist, PlaylistTrack, Track, UserLibrary, AlbumTrack, User

from api.routers.auth import get_current_user, require_premium
from api.routers.library import track_to_response
from api.schemas_v2.common import TelegramUser, PaginatedResponse
from api.schemas_v2.tracks import TrackResponse


router = APIRouter(tags=["Playlists"])


# Schemas
class PlaylistCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = False


class PlaylistUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


class PlaylistResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    track_count: int = 0
    total_duration: int = 0
    cover_url: Optional[str] = None
    is_public: bool = False
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PlaylistDetailResponse(PlaylistResponse):
    tracks: List[TrackResponse]


class PlaylistsListResponse(PaginatedResponse):
    items: List[PlaylistResponse]


class AddTrackRequest(BaseModel):
    track_id: int


class ReorderRequest(BaseModel):
    track_ids: List[int]


async def get_playlist_info(db: AsyncSession, playlist_id: int) -> tuple[int, int, Optional[str]]:
    """Get track count, duration, and cover for a playlist"""
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
    
    # First track's cover from enrichment
    cover_result = await db.execute(
        select(Track)
        .join(PlaylistTrack, PlaylistTrack.track_id == Track.id)
        .where(PlaylistTrack.playlist_id == playlist_id)
        .options(selectinload(Track.enrichment))
        .order_by(PlaylistTrack.position)
        .limit(1)
    )
    first_track = cover_result.scalar_one_or_none()
    cover_url = first_track.enrichment.cover_url if first_track and first_track.enrichment else None
    
    return track_count, total_duration, cover_url


@router.get("", response_model=PlaylistsListResponse)
async def get_my_playlists(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's playlists"""
    # Count
    total = await db.scalar(
        select(func.count(Playlist.id))
        .where(Playlist.owner_id == user.id)
    ) or 0
    
    # Get playlists
    offset = (page - 1) * per_page
    result = await db.execute(
        select(Playlist)
        .where(Playlist.owner_id == user.id)
        .order_by(Playlist.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    playlists = result.scalars().all()
    
    items = []
    for playlist in playlists:
        track_count, total_duration, cover_url = await get_playlist_info(db, playlist.id)
        items.append(PlaylistResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            track_count=track_count,
            total_duration=total_duration,
            cover_url=cover_url,
            is_public=playlist.is_public,
            created_at=playlist.created_at,
        ))
    
    return PlaylistsListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
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
    
    return PlaylistResponse(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        track_count=0,
        total_duration=0,
        cover_url=None,
        is_public=playlist.is_public,
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
    
    # Get cover from first track
    cover_url = None
    if rows:
        first_track = rows[0][0]
        if first_track.enrichment:
            cover_url = first_track.enrichment.cover_url
    
    return PlaylistDetailResponse(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        track_count=track_count,
        total_duration=total_duration,
        cover_url=cover_url,
        is_public=playlist.is_public,
        owner_id=owner.id,
        owner_name=owner.display_name,
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
    """
    playlist = await db.get(Playlist, playlist_id)
    
    if not playlist or playlist.owner_id != user.id:
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
    """Update playlist."""
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
    
    track_count, total_duration, cover_url = await get_playlist_info(db, playlist.id)
    
    return PlaylistResponse(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        track_count=track_count,
        total_duration=total_duration,
        cover_url=cover_url,
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
        track_count, total_duration, cover_url = await get_playlist_info(db, playlist.id)
        items.append(PlaylistResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            track_count=track_count,
            total_duration=total_duration,
            cover_url=cover_url,
            is_public=playlist.is_public,
            owner_id=owner.id,
            owner_name=owner.display_name,
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
        track_count, total_duration, cover_url = await get_playlist_info(db, playlist.id)
        items.append(PlaylistResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            track_count=track_count,
            total_duration=total_duration,
            cover_url=cover_url,
            is_public=playlist.is_public,
            owner_id=owner.id,
            owner_name=owner.display_name,
            created_at=playlist.created_at,
        ))
    
    return PlaylistsListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )

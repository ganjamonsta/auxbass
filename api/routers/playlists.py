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
from shared.models import Playlist, PlaylistTrack, Track, UserLibrary, AlbumTrack, User, PlaylistSubscription, UserChannel
from shared.config import get_settings

from api.routers.auth import get_current_user, require_premium
from api.routers.library import track_to_response
from api.schemas.common import TelegramUser, PaginatedResponse
from api.schemas.tracks import TrackResponse


router = APIRouter(tags=["Playlists"])


# Schemas
class PlaylistCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = True  # Default to public


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
    covers: List[str] = []  # Array of cover URLs for collage display
    tags: Optional[List[str]] = None  # Tags aggregated from playlist tracks
    is_public: bool = False
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None
    is_subscribed: bool = False  # Whether current user is subscribed
    is_owner: bool = False  # Whether current user is the owner
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


async def get_playlist_info(
    db: AsyncSession, 
    playlist_id: int, 
    playlist_cover_url: Optional[str] = None
) -> tuple[int, int, Optional[str], List[str]]:
    """
    Get track count, duration, cover, and covers array for a playlist.
    Returns: (track_count, total_duration, cover_url, covers)
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
        .where(PlaylistTrack.playlist_id == playlist_id)
        .options(selectinload(Track.enrichment))
        .order_by(PlaylistTrack.position)
        .limit(4)
    )
    track_covers = []
    for track in covers_result.scalars().all():
        if track.enrichment and track.enrichment.cover_url:
            track_covers.append(track.enrichment.cover_url)
    
    # Build covers array: if playlist has own cover, use it alone; otherwise use track covers
    if playlist_cover_url:
        covers = [playlist_cover_url]
        cover_url = playlist_cover_url
    else:
        covers = track_covers[:4]  # Up to 4 for collage
        cover_url = track_covers[0] if track_covers else None
    
    return track_count, total_duration, cover_url, covers


@router.get("", response_model=PlaylistsListResponse)
async def get_my_playlists(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    include_subscribed: bool = Query(True, description="Include subscribed playlists"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's public playlists (owned and subscribed). Private playlists are excluded."""
    # Count owned PUBLIC playlists only
    owned_count = await db.scalar(
        select(func.count(Playlist.id))
        .where(Playlist.owner_id == user.id)
        .where(Playlist.is_public == True)
    ) or 0
    
    # Count subscribed playlists
    subscribed_count = 0
    if include_subscribed:
        subscribed_count = await db.scalar(
            select(func.count(PlaylistSubscription.id))
            .where(PlaylistSubscription.user_id == user.id)
        ) or 0
    
    total = owned_count + subscribed_count
    
    # Get owned PUBLIC playlists only
    offset = (page - 1) * per_page
    result = await db.execute(
        select(Playlist, User)
        .join(User, User.id == Playlist.owner_id)
        .where(Playlist.owner_id == user.id)
        .where(Playlist.is_public == True)
        .order_by(Playlist.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    owned_rows = result.all()
    
    items = []
    for playlist, owner in owned_rows:
        track_count, total_duration, cover_url, covers = await get_playlist_info(db, playlist.id, playlist.cover_url)
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
    
    # Get subscribed playlists (if there's room on this page)
    if include_subscribed and len(items) < per_page:
        remaining = per_page - len(items)
        subscribed_offset = max(0, offset - owned_count)
        
        result = await db.execute(
            select(Playlist, User, PlaylistSubscription)
            .join(PlaylistSubscription, PlaylistSubscription.playlist_id == Playlist.id)
            .join(User, User.id == Playlist.owner_id)
            .where(PlaylistSubscription.user_id == user.id)
            .where(Playlist.is_public == True)  # Only include still-public playlists
            .order_by(PlaylistSubscription.subscribed_at.desc())
            .offset(subscribed_offset)
            .limit(remaining)
        )
        subscribed_rows = result.all()
        
        for playlist, owner, subscription in subscribed_rows:
            track_count, total_duration, cover_url, covers = await get_playlist_info(db, playlist.id, playlist.cover_url)
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
                is_owner=False,
                is_subscribed=True,
                created_at=playlist.created_at,
            ))
    
    return PlaylistsListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
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
        track_count, total_duration, cover_url, covers = await get_playlist_info(
            db, playlist.id, playlist.cover_url
        )
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
    
    # Build covers array and cover_url
    # If playlist has own cover, use it; otherwise use track covers for collage
    if playlist.cover_url:
        cover_url = playlist.cover_url
        covers = [playlist.cover_url]
    else:
        # Get up to 4 track covers for collage
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
    
    track_count, total_duration, cover_url, covers = await get_playlist_info(
        db, playlist.id, playlist.cover_url
    )
    
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


@router.post("/{playlist_id}/request-cover")
async def request_cover_upload(
    playlist_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Request cover upload from webapp.
    Sends message with ForceReply - user replies with photo.
    No database storage needed - playlist_id and channel_id encoded in message.
    """
    import httpx
    
    settings = get_settings()
    
    # Verify playlist ownership
    playlist = await db.get(Playlist, playlist_id)
    if not playlist or playlist.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Check user has connected channel
    channel = await db.scalar(
        select(UserChannel).where(
            UserChannel.user_id == user.id,
            UserChannel.is_active == True
        )
    )
    
    if not channel:
        raise HTTPException(
            status_code=400, 
            detail="Подключите канал для загрузки обложек. Используйте /channel в боте."
        )
    
    # Send message with ForceReply - encode data in message for parsing on reply
    # The cover:playlist_id:channel_id pattern is parsed by bot when user replies with photo
    bot_api_url = f"{settings.telegram_api_url}/bot{settings.bot_token}/sendMessage"
    message_text = (
        f"📷 <b>Загрузка обложки для плейлиста</b>\n\n"
        f"🎵 <i>{playlist.name}</i>\n\n"
        f"Ответьте на это сообщение фотографией.\n"
        f"Я автоматически обрежу изображение до квадрата.\n\n"
        f"<i>cover:{playlist_id}:{channel.channel_id}</i>"
    )
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(bot_api_url, json={
                "chat_id": user.id,
                "text": message_text,
                "parse_mode": "HTML",
                "reply_markup": {
                    "force_reply": True,
                    "selective": True,
                    "input_field_placeholder": "Отправьте фото..."
                }
            })
            response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Не удалось отправить сообщение: {e}")
    
    return {"status": "pending", "message": "Ответьте на сообщение фото"}


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
        track_count, total_duration, cover_url, covers = await get_playlist_info(db, playlist.id, playlist.cover_url)
        
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
        track_count, total_duration, cover_url, covers = await get_playlist_info(db, playlist.id, playlist.cover_url)
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


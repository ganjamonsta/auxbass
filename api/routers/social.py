"""
TG Player API v2 - Social Router

User following, friends library access.
"""
import logging
from typing import Optional, List
from datetime import datetime

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select, func, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.config import get_settings
from shared.database import get_db
from shared.models import (
    User, UserFollow, UserLibrary, Track, TrackEnrichment,
    Playlist, PlaylistTrack, Album, AlbumTrack
)

from api.routers.auth import get_current_user, require_premium

logger = logging.getLogger(__name__)
from api.routers.library import track_to_response
from api.schemas_v2.common import TelegramUser, PaginatedResponse
from api.schemas_v2.tracks import TrackResponse


router = APIRouter(prefix="/social", tags=["Social"])


# ============== Schemas ==============

class UserProfileResponse(BaseModel):
    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: str
    is_following: bool = False
    track_count: int = 0
    playlist_count: int = 0
    followers_count: int = 0
    following_count: int = 0
    
    class Config:
        from_attributes = True


class UserListResponse(PaginatedResponse):
    items: List[UserProfileResponse]


class FollowRequest(BaseModel):
    user_id: int


class FriendLibraryResponse(BaseModel):
    user: UserProfileResponse
    recent_tracks: List[TrackResponse]
    public_playlists: List[dict]


# ============== Helper Functions ==============

async def get_user_stats(db: AsyncSession, user_id: int) -> dict:
    """Get user's library statistics"""
    track_count = await db.scalar(
        select(func.count(UserLibrary.id))
        .where(UserLibrary.user_id == user_id)
    ) or 0
    
    playlist_count = await db.scalar(
        select(func.count(Playlist.id))
        .where(Playlist.owner_id == user_id, Playlist.is_public == True)
    ) or 0
    
    followers_count = await db.scalar(
        select(func.count(UserFollow.id))
        .where(UserFollow.following_id == user_id)
    ) or 0
    
    following_count = await db.scalar(
        select(func.count(UserFollow.id))
        .where(UserFollow.follower_id == user_id)
    ) or 0
    
    return {
        "track_count": track_count,
        "playlist_count": playlist_count,
        "followers_count": followers_count,
        "following_count": following_count,
    }


async def is_following(db: AsyncSession, follower_id: int, following_id: int) -> bool:
    """Check if user is following another user"""
    result = await db.scalar(
        select(UserFollow.id)
        .where(
            UserFollow.follower_id == follower_id,
            UserFollow.following_id == following_id
        )
    )
    return result is not None


# ============== Notification Helper ==============

async def send_subscription_notification(
    target_user_id: int,
    follower_name: str,
    follower_username: Optional[str] = None
):
    """
    Send notification to user about new follower via Telegram Bot API.
    This runs in background to not block the API response.
    """
    settings = get_settings()
    
    # Build notification message
    if follower_username:
        follower_link = f"<a href='https://t.me/{follower_username}'>{follower_name}</a>"
    else:
        follower_link = f"<b>{follower_name}</b>"
    
    message_text = (
        f"👤 <b>Новый подписчик!</b>\n\n"
        f"{follower_link} подписался на вашу медиатеку."
    )
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{settings.telegram_api_url}/bot{settings.bot_token}/sendMessage",
                json={
                    "chat_id": target_user_id,
                    "text": message_text,
                    "parse_mode": "HTML",
                    "disable_notification": False
                },
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.warning(f"Failed to send notification: {text}")
    except Exception as e:
        logger.error(f"Error sending subscription notification: {e}")


# ============== Following Endpoints ==============

@router.post("/follow")
async def follow_user(
    data: FollowRequest,
    background_tasks: BackgroundTasks,
    user: TelegramUser = Depends(require_premium),
    db: AsyncSession = Depends(get_db),
):
    """Follow a user. Requires connected channel."""
    if data.user_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    
    # Check if target user exists
    target = await db.get(User, data.user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already following
    existing = await db.scalar(
        select(UserFollow)
        .where(
            UserFollow.follower_id == user.id,
            UserFollow.following_id == data.user_id
        )
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already following this user")
    
    # Create follow
    follow = UserFollow(
        follower_id=user.id,
        following_id=data.user_id,
    )
    db.add(follow)
    await db.commit()
    
    # Send notification if target user has notifications enabled
    if target.notify_subscription:
        # Get follower info for notification
        follower = await db.get(User, user.id)
        if follower:
            follower_name = follower.display_name
            follower_username = follower.username
            background_tasks.add_task(
                send_subscription_notification,
                target.id,
                follower_name,
                follower_username
            )
    
    return {"status": "followed", "user_id": data.user_id}


@router.post("/unfollow")
async def unfollow_user(
    data: FollowRequest,
    user: TelegramUser = Depends(require_premium),
    db: AsyncSession = Depends(get_db),
):
    """Unfollow a user. Requires connected channel."""
    result = await db.execute(
        delete(UserFollow)
        .where(
            UserFollow.follower_id == user.id,
            UserFollow.following_id == data.user_id
        )
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Not following this user")
    
    await db.commit()
    
    return {"status": "unfollowed", "user_id": data.user_id}


@router.get("/following", response_model=UserListResponse)
async def get_following(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get users I'm following"""
    # Count
    total = await db.scalar(
        select(func.count(UserFollow.id))
        .where(UserFollow.follower_id == user.id)
    ) or 0
    
    # Get following
    offset = (page - 1) * per_page
    result = await db.execute(
        select(User)
        .join(UserFollow, UserFollow.following_id == User.id)
        .where(UserFollow.follower_id == user.id)
        .order_by(UserFollow.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    users = result.scalars().all()
    
    items = []
    for u in users:
        stats = await get_user_stats(db, u.id)
        items.append(UserProfileResponse(
            id=u.id,
            username=u.username,
            first_name=u.first_name,
            last_name=u.last_name,
            display_name=u.display_name,
            is_following=True,  # We're getting users we follow
            **stats,
        ))
    
    return UserListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/followers", response_model=UserListResponse)
async def get_followers(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get my followers"""
    # Count
    total = await db.scalar(
        select(func.count(UserFollow.id))
        .where(UserFollow.following_id == user.id)
    ) or 0
    
    # Get followers
    offset = (page - 1) * per_page
    result = await db.execute(
        select(User)
        .join(UserFollow, UserFollow.follower_id == User.id)
        .where(UserFollow.following_id == user.id)
        .order_by(UserFollow.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    users = result.scalars().all()
    
    items = []
    for u in users:
        stats = await get_user_stats(db, u.id)
        following = await is_following(db, user.id, u.id)
        items.append(UserProfileResponse(
            id=u.id,
            username=u.username,
            first_name=u.first_name,
            last_name=u.last_name,
            display_name=u.display_name,
            is_following=following,
            **stats,
        ))
    
    return UserListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )


# ============== User Profile & Library ==============

@router.get("/user/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user profile"""
    target = await db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    stats = await get_user_stats(db, user_id)
    following = await is_following(db, user.id, user_id) if user_id != user.id else False
    
    return UserProfileResponse(
        id=target.id,
        username=target.username,
        first_name=target.first_name,
        last_name=target.last_name,
        display_name=target.display_name,
        is_following=following,
        **stats,
    )


@router.get("/user/{user_id}/library")
async def get_user_library(
    user_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user's library (public tracks).
    For now, all tracks are visible if user has any public content.
    """
    target = await db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user has hidden their profile
    if target.hide_profile and user_id != user.id:
        raise HTTPException(status_code=403, detail="Пользователь скрыл свой профиль")
    
    # Count tracks
    total = await db.scalar(
        select(func.count(UserLibrary.id))
        .where(UserLibrary.user_id == user_id)
    ) or 0
    
    # Get tracks with enrichment
    offset = (page - 1) * per_page
    result = await db.execute(
        select(Track, UserLibrary)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user_id)
        .options(
            selectinload(Track.enrichment),
            selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
        )
        .order_by(UserLibrary.added_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    rows = result.unique().all()
    
    # For viewing friend's library, we pass None for lib_entry to not show
    # the viewer's own like status
    viewer_lib_entry = None
    items = []
    for track, lib_entry in rows:
        # Get viewer's library entry for this track
        viewer_entry = await db.scalar(
            select(UserLibrary)
            .where(UserLibrary.user_id == user.id, UserLibrary.track_id == track.id)
        )
        items.append(track_to_response(track, viewer_entry))
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "user": {
            "id": target.id,
            "display_name": target.display_name,
        }
    }


@router.get("/user/{user_id}/albums")
async def get_user_albums(
    user_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get albums that have tracks in user's library"""
    target = await db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user has hidden their profile
    if target.hide_profile and user_id != user.id:
        raise HTTPException(status_code=403, detail="Пользователь скрыл свой профиль")
    
    # Get unique albums from user's library
    offset = (page - 1) * per_page
    
    # Count unique albums
    total = await db.scalar(
        select(func.count(func.distinct(Album.id)))
        .join(AlbumTrack, AlbumTrack.album_id == Album.id)
        .join(Track, Track.id == AlbumTrack.track_id)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user_id)
    ) or 0
    
    # Get albums with track counts
    result = await db.execute(
        select(
            Album,
            func.count(func.distinct(Track.id)).label("track_count")
        )
        .join(AlbumTrack, AlbumTrack.album_id == Album.id)
        .join(Track, Track.id == AlbumTrack.track_id)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user_id)
        .group_by(Album.id)
        .order_by(func.count(func.distinct(Track.id)).desc())
        .offset(offset)
        .limit(per_page)
    )
    rows = result.all()
    
    items = []
    for album, track_count in rows:
        items.append({
            "id": album.id,
            "name": album.name,
            "artist": album.artist,
            "cover_url": album.cover_url,
            "release_date": album.release_date,
            "track_count": track_count,
            "total_tracks": album.total_tracks,
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "user": {
            "id": target.id,
            "display_name": target.display_name,
        }
    }


# ============== Search Users ==============

@router.get("/search")
async def search_users(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search users by username or name"""
    search_pattern = f"%{q}%"
    
    # Count matching users (exclude hidden users)
    total = await db.scalar(
        select(func.count(User.id))
        .where(
            User.hide_from_search == False,
            User.id != user.id,  # Exclude self
            or_(
                User.username.ilike(search_pattern),
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern),
            )
        )
    ) or 0
    
    # Get matching users (exclude hidden users)
    offset = (page - 1) * per_page
    result = await db.execute(
        select(User)
        .where(
            User.hide_from_search == False,
            User.id != user.id,  # Exclude self
            or_(
                User.username.ilike(search_pattern),
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern),
            )
        )
        .order_by(User.username)
        .offset(offset)
        .limit(per_page)
    )
    users = result.scalars().all()
    
    items = []
    for u in users:
        stats = await get_user_stats(db, u.id)
        following = await is_following(db, user.id, u.id) if u.id != user.id else False
        items.append(UserProfileResponse(
            id=u.id,
            username=u.username,
            first_name=u.first_name,
            last_name=u.last_name,
            display_name=u.display_name,
            is_following=following,
            **stats,
        ))
    
    return UserListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )

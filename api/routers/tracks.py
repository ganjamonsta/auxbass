"""
TG Player API - Tracks Router
Supports global shared library - all users can see and play each other's tracks
"""
import re
import aiohttp
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import get_db
from shared.models import Track, UserLibrary, User
from shared.config import get_settings

from .auth import get_current_user, TelegramUser


router = APIRouter()
settings = get_settings()

# Cache for artist images
_artist_image_cache: dict[str, str] = {}


def sanitize_input(value: str) -> str:
    """Sanitize input to prevent SQL injection"""
    if not value:
        return ""
    value = value.replace('%', r'\%').replace('_', r'\_')
    return value[:200].strip()


# Pydantic models
class TrackBase(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None


class UploaderInfo(BaseModel):
    """Info about who uploaded the track"""
    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class ForwardSourceInfo(BaseModel):
    """Info about from whom the track was forwarded"""
    forward_from_id: Optional[int] = None
    forward_from_username: Optional[str] = None
    forward_from_name: Optional[str] = None
    forward_from_type: Optional[str] = None  # user, bot, channel
    
    class Config:
        from_attributes = True


class TrackResponse(TrackBase):
    id: int
    file_id: str
    duration: Optional[int] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    cover_url: Optional[str] = None
    enrichment_status: Optional[str] = None
    is_liked: bool = False
    is_unavailable: bool = False
    is_public: bool = True
    play_count: int = 0  # Global play count
    in_library: bool = False  # Is in current user's library
    uploader: Optional[UploaderInfo] = None  # Who uploaded
    forward_source: Optional[ForwardSourceInfo] = None  # Forwarded from
    created_at: datetime
    
    class Config:
        from_attributes = True


class TrackUpdate(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None
    is_public: Optional[bool] = None


class TracksListResponse(BaseModel):
    items: List[TrackResponse]
    total: int
    page: int
    per_page: int


def track_to_response(track: Track, user_library: Optional[UserLibrary] = None, user_id: int = None) -> TrackResponse:
    """Convert Track model to response with user-specific data"""
    uploader_info = None
    if track.uploader:
        uploader_info = UploaderInfo(
            id=track.uploader.id,
            username=track.uploader.username,
            first_name=track.uploader.first_name,
        )
    
    # Forward source info
    forward_source = None
    if track.forward_from_type:
        forward_source = ForwardSourceInfo(
            forward_from_id=track.forward_from_id,
            forward_from_username=track.forward_from_username,
            forward_from_name=track.forward_from_name,
            forward_from_type=track.forward_from_type,
        )
    
    return TrackResponse(
        id=track.id,
        file_id=track.file_id,
        title=track.title,
        artist=track.artist,
        album=track.album,
        genre=track.genre,
        duration=track.duration,
        file_size=track.file_size,
        mime_type=track.mime_type,
        cover_url=track.cover_url,
        enrichment_status=track.enrichment_status,
        is_liked=user_library.is_liked if user_library else False,
        is_unavailable=track.is_unavailable,
        is_public=track.is_public,
        play_count=track.play_count,
        in_library=user_library is not None,
        uploader=uploader_info,
        forward_source=forward_source,
        created_at=track.created_at,
    )


# ============== MY LIBRARY ENDPOINTS ==============

@router.get("", response_model=TracksListResponse)
async def get_my_tracks(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    artist: Optional[str] = None,
    genre: Optional[str] = None,
    sort_by: str = Query("added_at", pattern="^(added_at|title|artist|duration|play_count|last_played_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get tracks from user's personal library"""
    
    # Join UserLibrary with Track
    query = (
        select(Track, UserLibrary)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
        .options(selectinload(Track.uploader))
    )
    count_query = (
        select(func.count(UserLibrary.id))
        .join(Track, Track.id == UserLibrary.track_id)
        .where(UserLibrary.user_id == user.id)
    )
    
    # Apply search filter
    if search:
        safe_search = sanitize_input(search)
        if safe_search:
            terms = safe_search.split()
            for term in terms:
                term_filter = or_(
                    Track.title.ilike(f"%{term}%"),
                    Track.artist.ilike(f"%{term}%"),
                    Track.album.ilike(f"%{term}%"),
                )
                query = query.where(term_filter)
                count_query = count_query.where(term_filter)
    
    # Apply artist filter
    if artist:
        safe_artist = sanitize_input(artist)
        if safe_artist:
            query = query.where(Track.artist.ilike(f"%{safe_artist}%"))
            count_query = count_query.where(Track.artist.ilike(f"%{safe_artist}%"))
    
    # Apply genre filter
    if genre:
        safe_genre = sanitize_input(genre)
        if safe_genre:
            query = query.where(Track.genre.ilike(f"%{safe_genre}%"))
            count_query = count_query.where(Track.genre.ilike(f"%{safe_genre}%"))
    
    total = await db.scalar(count_query)
    
    # Apply sorting (some fields from UserLibrary, some from Track)
    if sort_by == "added_at":
        sort_column = UserLibrary.added_at
    elif sort_by == "last_played_at":
        sort_column = UserLibrary.last_played_at
    elif sort_by == "play_count":
        sort_column = UserLibrary.play_count
    else:
        sort_column = getattr(Track, sort_by)
    
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    result = await db.execute(query)
    rows = result.all()
    
    items = [track_to_response(track, lib_entry, user.id) for track, lib_entry in rows]
    
    return TracksListResponse(
        items=items,
        total=total or 0,
        page=page,
        per_page=per_page,
    )


# ============== GLOBAL LIBRARY ENDPOINTS ==============

@router.get("/global", response_model=TracksListResponse)
async def get_global_tracks(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    artist: Optional[str] = None,
    genre: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(created_at|title|artist|duration|play_count)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all public tracks from global library"""
    
    # Base query - only public tracks
    query = (
        select(Track)
        .where(Track.is_public == True)
        .where(Track.is_unavailable == False)
        .options(selectinload(Track.uploader))
    )
    count_query = (
        select(func.count(Track.id))
        .where(Track.is_public == True)
        .where(Track.is_unavailable == False)
    )
    
    # Apply search filter
    if search:
        safe_search = sanitize_input(search)
        if safe_search:
            terms = safe_search.split()
            for term in terms:
                term_filter = or_(
                    Track.title.ilike(f"%{term}%"),
                    Track.artist.ilike(f"%{term}%"),
                    Track.album.ilike(f"%{term}%"),
                )
                query = query.where(term_filter)
                count_query = count_query.where(term_filter)
    
    if artist:
        safe_artist = sanitize_input(artist)
        if safe_artist:
            query = query.where(Track.artist.ilike(f"%{safe_artist}%"))
            count_query = count_query.where(Track.artist.ilike(f"%{safe_artist}%"))
    
    if genre:
        safe_genre = sanitize_input(genre)
        if safe_genre:
            query = query.where(Track.genre.ilike(f"%{safe_genre}%"))
            count_query = count_query.where(Track.genre.ilike(f"%{safe_genre}%"))
    
    total = await db.scalar(count_query)
    
    # Sorting
    sort_column = getattr(Track, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    result = await db.execute(query)
    tracks = result.scalars().all()
    
    # Get user's library entries for these tracks
    track_ids = [t.id for t in tracks]
    lib_result = await db.execute(
        select(UserLibrary)
        .where(UserLibrary.user_id == user.id)
        .where(UserLibrary.track_id.in_(track_ids))
    )
    user_lib = {lib.track_id: lib for lib in lib_result.scalars().all()}
    
    items = [track_to_response(t, user_lib.get(t.id), user.id) for t in tracks]
    
    return TracksListResponse(
        items=items,
        total=total or 0,
        page=page,
        per_page=per_page,
    )


@router.get("/global/recent")
async def get_recent_uploads(
    limit: int = Query(20, ge=1, le=50),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recently uploaded tracks globally"""
    result = await db.execute(
        select(Track)
        .where(Track.is_public == True)
        .where(Track.is_unavailable == False)
        .options(selectinload(Track.uploader))
        .order_by(Track.created_at.desc())
        .limit(limit)
    )
    tracks = result.scalars().all()
    
    # Get user's library entries
    track_ids = [t.id for t in tracks]
    lib_result = await db.execute(
        select(UserLibrary)
        .where(UserLibrary.user_id == user.id)
        .where(UserLibrary.track_id.in_(track_ids))
    )
    user_lib = {lib.track_id: lib for lib in lib_result.scalars().all()}
    
    return [track_to_response(t, user_lib.get(t.id), user.id) for t in tracks]


@router.get("/global/popular")
async def get_popular_tracks(
    limit: int = Query(20, ge=1, le=50),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get most played tracks globally"""
    result = await db.execute(
        select(Track)
        .where(Track.is_public == True)
        .where(Track.is_unavailable == False)
        .where(Track.play_count > 0)
        .options(selectinload(Track.uploader))
        .order_by(Track.play_count.desc())
        .limit(limit)
    )
    tracks = result.scalars().all()
    
    track_ids = [t.id for t in tracks]
    lib_result = await db.execute(
        select(UserLibrary)
        .where(UserLibrary.user_id == user.id)
        .where(UserLibrary.track_id.in_(track_ids))
    )
    user_lib = {lib.track_id: lib for lib in lib_result.scalars().all()}
    
    return [track_to_response(t, user_lib.get(t.id), user.id) for t in tracks]


@router.get("/global/stats")
async def get_global_stats(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get global library statistics"""
    total_tracks = await db.scalar(
        select(func.count(Track.id)).where(Track.is_public == True)
    )
    total_users = await db.scalar(
        select(func.count(func.distinct(Track.user_id)))
    )
    total_plays = await db.scalar(
        select(func.sum(Track.play_count))
    )
    
    # User's contribution
    my_uploads = await db.scalar(
        select(func.count(Track.id)).where(Track.user_id == user.id)
    )
    my_library_size = await db.scalar(
        select(func.count(UserLibrary.id)).where(UserLibrary.user_id == user.id)
    )
    
    return {
        "total_tracks": total_tracks or 0,
        "total_users": total_users or 0,
        "total_plays": total_plays or 0,
        "my_uploads": my_uploads or 0,
        "my_library_size": my_library_size or 0,
    }


class UserStatsResponse(BaseModel):
    """User statistics for the global library"""
    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    track_count: int = 0
    total_plays: int = 0
    
    class Config:
        from_attributes = True


@router.get("/global/users", response_model=List[UserStatsResponse])
async def get_top_users(
    limit: int = Query(20, ge=1, le=50),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get top users by upload count with their stats"""
    # Get users with their track counts and total plays
    result = await db.execute(
        select(
            User,
            func.count(Track.id).label("track_count"),
            func.coalesce(func.sum(Track.play_count), 0).label("total_plays")
        )
        .join(Track, Track.user_id == User.id)
        .where(Track.is_public == True)
        .group_by(User.id)
        .order_by(func.count(Track.id).desc())
        .limit(limit)
    )
    
    users = []
    for row in result.all():
        user_obj = row[0]
        users.append(UserStatsResponse(
            id=user_obj.id,
            username=user_obj.username,
            first_name=user_obj.first_name,
            track_count=row[1],
            total_plays=row[2],
        ))
    
    return users


@router.get("/global/users/{user_id}/tracks", response_model=List[TrackResponse])
async def get_user_tracks(
    user_id: int,
    limit: int = Query(50, ge=1, le=100),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get tracks uploaded by a specific user"""
    result = await db.execute(
        select(Track)
        .options(selectinload(Track.uploader))
        .where(Track.user_id == user_id)
        .where(Track.is_public == True)
        .order_by(Track.created_at.desc())
        .limit(limit)
    )
    tracks = result.scalars().all()
    
    # Get user's library status for these tracks
    track_ids = [t.id for t in tracks]
    lib_result = await db.execute(
        select(UserLibrary)
        .where(UserLibrary.user_id == user.id)
        .where(UserLibrary.track_id.in_(track_ids))
    )
    user_lib = {lib.track_id: lib for lib in lib_result.scalars().all()}
    
    return [track_to_response(t, user_lib.get(t.id), user.id) for t in tracks]


# ============== LIBRARY MANAGEMENT ==============

@router.post("/{track_id}/add-to-library")
async def add_to_library(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a track from global library to user's personal library"""
    # Check track exists and is public
    track = await db.scalar(
        select(Track).where(Track.id == track_id)
    )
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    if not track.is_public and track.user_id != user.id:
        raise HTTPException(status_code=403, detail="This track is private")
    
    # Check if already in library
    existing = await db.scalar(
        select(UserLibrary).where(
            UserLibrary.user_id == user.id,
            UserLibrary.track_id == track_id
        )
    )
    
    if existing:
        return {"status": "already_in_library", "track_id": track_id}
    
    # Add to library
    lib_entry = UserLibrary(
        user_id=user.id,
        track_id=track_id,
        source="added",
    )
    db.add(lib_entry)
    await db.commit()
    
    return {"status": "added", "track_id": track_id}


@router.delete("/{track_id}/remove-from-library")
async def remove_from_library(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a track from user's personal library (doesn't delete the track)"""
    lib_entry = await db.scalar(
        select(UserLibrary).where(
            UserLibrary.user_id == user.id,
            UserLibrary.track_id == track_id
        )
    )
    
    if not lib_entry:
        raise HTTPException(status_code=404, detail="Track not in your library")
    
    await db.delete(lib_entry)
    await db.commit()
    
    return {"status": "removed", "track_id": track_id}


# ============== ARTISTS & GENRES ==============

@router.get("/artists")
async def get_artists(
    scope: str = Query("library", pattern="^(library|global)$"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of unique artists from library or global"""
    
    if scope == "library":
        result = await db.execute(
            select(Track.artist)
            .join(UserLibrary, UserLibrary.track_id == Track.id)
            .where(UserLibrary.user_id == user.id)
            .where(Track.artist.isnot(None))
        )
    else:
        result = await db.execute(
            select(Track.artist)
            .where(Track.is_public == True)
            .where(Track.artist.isnot(None))
        )
    
    # Split and count with case-insensitive grouping
    artist_counts = {}
    artist_canonical = {}  # Maps lowercase -> canonical (most common) case
    
    for (artist_str,) in result.all():
        artists = re.split(r'\s*[,&]\s*|\s+(?:feat\.?|ft\.?|x|vs\.?)\s+', artist_str, flags=re.IGNORECASE)
        for artist in artists:
            artist = artist.strip()
            if artist:
                lower_name = artist.lower()
                # Track canonical form (first seen or most popular capitalization)
                if lower_name not in artist_canonical:
                    artist_canonical[lower_name] = artist
                artist_counts[lower_name] = artist_counts.get(lower_name, 0) + 1
    
    sorted_artists = sorted(artist_counts.items(), key=lambda x: (-x[1], x[0]))
    
    return [{"artist": artist_canonical[name], "count": count, "image_url": None} for name, count in sorted_artists]


async def fetch_artist_image(artist_name: str) -> Optional[str]:
    """Fetch artist image from Last.fm API"""
    if not settings.lastfm_api_key:
        return None
    
    cache_key = artist_name.lower()
    if cache_key in _artist_image_cache:
        return _artist_image_cache[cache_key]
    
    try:
        url = "https://ws.audioscrobbler.com/2.0/"
        params = {
            "method": "artist.search",
            "artist": artist_name,
            "api_key": settings.lastfm_api_key,
            "format": "json",
            "limit": 1
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=5) as resp:
                if resp.status != 200:
                    return None
                
                data = await resp.json()
                artists = data.get("results", {}).get("artistmatches", {}).get("artist", [])
                
                if artists and len(artists) > 0:
                    images = artists[0].get("image", [])
                    for img in reversed(images):
                        if img.get("#text") and img.get("size") in ["large", "extralarge", "mega"]:
                            image_url = img["#text"]
                            _artist_image_cache[cache_key] = image_url
                            return image_url
                    for img in reversed(images):
                        if img.get("#text"):
                            image_url = img["#text"]
                            _artist_image_cache[cache_key] = image_url
                            return image_url
                
                _artist_image_cache[cache_key] = ""
                return None
                
    except Exception:
        return None


@router.get("/artist-image/{artist_name:path}")
async def get_artist_image(
    artist_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Get artist image URL"""
    image_url = await fetch_artist_image(artist_name)
    
    if image_url and "2a96cbd8b46e442fc41c2b86b821562f" not in image_url:
        return {"artist": artist_name, "image_url": image_url}
    
    result = await db.execute(
        select(Track.cover_url)
        .where(Track.artist.ilike(f"%{artist_name}%"))
        .where(Track.cover_url.isnot(None))
        .where(Track.cover_url != "")
        .order_by(Track.play_count.desc())
        .limit(1)
    )
    track_cover = result.scalar_one_or_none()
    
    return {"artist": artist_name, "image_url": track_cover}


@router.get("/genres")
async def get_genres(
    scope: str = Query("library", pattern="^(library|global)$"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of unique genres from library or global"""
    
    if scope == "library":
        result = await db.execute(
            select(Track.genre, func.count(Track.id).label("count"))
            .join(UserLibrary, UserLibrary.track_id == Track.id)
            .where(UserLibrary.user_id == user.id)
            .where(Track.genre.isnot(None))
            .group_by(Track.genre)
            .order_by(func.count(Track.id).desc())
        )
    else:
        result = await db.execute(
            select(Track.genre, func.count(Track.id).label("count"))
            .where(Track.is_public == True)
            .where(Track.genre.isnot(None))
            .group_by(Track.genre)
            .order_by(func.count(Track.id).desc())
        )
    
    return [{"genre": row[0], "count": row[1]} for row in result.all()]


# ============== ENRICHMENT STATUS ==============

@router.get("/enrichment/status")
async def get_enrichment_status(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get enrichment status for tracks uploaded by user"""
    result = await db.execute(
        select(
            Track.enrichment_status,
            func.count(Track.id)
        )
        .where(Track.user_id == user.id)
        .group_by(Track.enrichment_status)
    )
    
    stats = {row[0] or "pending": row[1] for row in result.all()}
    total = sum(stats.values())
    
    return {
        "pending": stats.get("pending", 0),
        "processing": stats.get("processing", 0),
        "completed": stats.get("completed", 0),
        "failed": stats.get("failed", 0),
        "total": total,
        "progress": round(stats.get("completed", 0) / total * 100) if total > 0 else 100
    }


# ============== HISTORY & LIKED ==============

@router.get("/history")
async def get_listening_history(
    limit: int = Query(50, ge=1, le=100),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get listening history from user's library"""
    result = await db.execute(
        select(Track, UserLibrary)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
        .where(UserLibrary.last_played_at.isnot(None))
        .options(selectinload(Track.uploader))
        .order_by(UserLibrary.last_played_at.desc())
        .limit(limit)
    )
    
    rows = result.all()
    return [track_to_response(track, lib_entry, user.id) for track, lib_entry in rows]


@router.get("/liked")
async def get_liked_tracks(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all liked tracks from user's library"""
    result = await db.execute(
        select(Track, UserLibrary)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(UserLibrary.user_id == user.id)
        .where(UserLibrary.is_liked == True)
        .options(selectinload(Track.uploader))
        .order_by(UserLibrary.liked_at.desc())
    )
    
    rows = result.all()
    return [track_to_response(track, lib_entry, user.id) for track, lib_entry in rows]


@router.post("/{track_id}/like")
async def like_track(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Like a track (adds to library if not already there)"""
    track = await db.scalar(select(Track).where(Track.id == track_id))
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    if not track.is_public and track.user_id != user.id:
        raise HTTPException(status_code=403, detail="Track is private")
    
    # Get or create library entry
    lib_entry = await db.scalar(
        select(UserLibrary).where(
            UserLibrary.user_id == user.id,
            UserLibrary.track_id == track_id
        )
    )
    
    if not lib_entry:
        lib_entry = UserLibrary(
            user_id=user.id,
            track_id=track_id,
            source="liked",
        )
        db.add(lib_entry)
    
    lib_entry.is_liked = True
    lib_entry.liked_at = datetime.utcnow()
    
    await db.commit()
    
    return {"status": "liked", "id": track_id, "is_liked": True, "in_library": True}


@router.delete("/{track_id}/like")
async def unlike_track(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unlike a track"""
    lib_entry = await db.scalar(
        select(UserLibrary).where(
            UserLibrary.user_id == user.id,
            UserLibrary.track_id == track_id
        )
    )
    
    if not lib_entry:
        raise HTTPException(status_code=404, detail="Track not in your library")
    
    lib_entry.is_liked = False
    lib_entry.liked_at = None
    
    await db.commit()
    
    return {"status": "unliked", "id": track_id, "is_liked": False}


# ============== SINGLE TRACK OPERATIONS ==============

@router.get("/{track_id}", response_model=TrackResponse)
async def get_track(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get single track by ID (any public track or own)"""
    track = await db.scalar(
        select(Track)
        .where(Track.id == track_id)
        .options(selectinload(Track.uploader))
    )
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    if not track.is_public and track.user_id != user.id:
        raise HTTPException(status_code=403, detail="Track is private")
    
    lib_entry = await db.scalar(
        select(UserLibrary).where(
            UserLibrary.user_id == user.id,
            UserLibrary.track_id == track_id
        )
    )
    
    return track_to_response(track, lib_entry, user.id)


@router.put("/{track_id}", response_model=TrackResponse)
async def update_track(
    track_id: int,
    data: TrackUpdate,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update track metadata (only uploader can update)"""
    track = await db.scalar(
        select(Track)
        .where(Track.id == track_id, Track.user_id == user.id)
        .options(selectinload(Track.uploader))
    )
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found or you're not the uploader")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(track, field, value)
    
    await db.commit()
    await db.refresh(track)
    
    lib_entry = await db.scalar(
        select(UserLibrary).where(
            UserLibrary.user_id == user.id,
            UserLibrary.track_id == track_id
        )
    )
    
    return track_to_response(track, lib_entry, user.id)


@router.delete("/{track_id}")
async def delete_track(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete track (only uploader can delete)"""
    track = await db.scalar(
        select(Track).where(Track.id == track_id, Track.user_id == user.id)
    )
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found or you're not the uploader")
    
    await db.delete(track)
    await db.commit()
    
    return {"status": "deleted", "id": track_id}


@router.post("/{track_id}/mark-unavailable")
async def mark_track_unavailable(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a track as unavailable"""
    track = await db.scalar(
        select(Track).where(Track.id == track_id, Track.user_id == user.id)
    )
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found or you're not the uploader")
    
    track.is_unavailable = True
    await db.commit()
    
    return {"status": "marked_unavailable", "id": track_id}


@router.get("/unavailable/list")
async def get_unavailable_tracks(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get unavailable tracks uploaded by user"""
    result = await db.execute(
        select(Track)
        .where(Track.user_id == user.id)
        .where(Track.is_unavailable == True)
        .options(selectinload(Track.uploader))
    )
    
    tracks = result.scalars().all()
    
    lib_result = await db.execute(
        select(UserLibrary)
        .where(UserLibrary.user_id == user.id)
        .where(UserLibrary.track_id.in_([t.id for t in tracks]))
    )
    user_lib = {lib.track_id: lib for lib in lib_result.scalars().all()}
    
    return [track_to_response(t, user_lib.get(t.id), user.id) for t in tracks]


@router.delete("/unavailable/all")
async def delete_all_unavailable_tracks(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete all unavailable tracks uploaded by user"""
    from sqlalchemy import delete as sql_delete
    
    result = await db.execute(
        sql_delete(Track)
        .where(Track.user_id == user.id)
        .where(Track.is_unavailable == True)
    )
    
    await db.commit()
    
    return {"status": "deleted", "count": result.rowcount}

"""
TG Player API - Tracks Router
"""
import re
import aiohttp
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import get_db
from shared.models import Track
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
    # Escape % and _ for LIKE queries
    value = value.replace('%', r'\%').replace('_', r'\_')
    return value[:200].strip()


# Pydantic models
class TrackBase(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None


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
    created_at: datetime
    
    class Config:
        from_attributes = True


class TrackUpdate(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None


class TracksListResponse(BaseModel):
    items: List[TrackResponse]
    total: int
    page: int
    per_page: int


@router.get("", response_model=TracksListResponse)
async def get_tracks(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    artist: Optional[str] = None,
    genre: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(created_at|title|artist|duration|play_count|last_played_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's tracks with pagination and filters"""
    
    # Base query
    query = select(Track).where(Track.user_id == user.id)
    count_query = select(func.count(Track.id)).where(Track.user_id == user.id)
    
    # Apply search filter (sanitized)
    if search:
        safe_search = sanitize_input(search)
        if safe_search:
            # Split by spaces to support multi-term search
            terms = safe_search.split()
            for term in terms:
                term_filter = or_(
                    Track.title.ilike(f"%{term}%"),
                    Track.artist.ilike(f"%{term}%"),
                    Track.album.ilike(f"%{term}%"),
                )
                query = query.where(term_filter)
                count_query = count_query.where(term_filter)
    
    # Apply artist filter (sanitized)
    if artist:
        safe_artist = sanitize_input(artist)
        if safe_artist:
            query = query.where(Track.artist.ilike(f"%{safe_artist}%"))
            count_query = count_query.where(Track.artist.ilike(f"%{safe_artist}%"))
    
    # Apply genre filter (sanitized)
    if genre:
        safe_genre = sanitize_input(genre)
        if safe_genre:
            query = query.where(Track.genre.ilike(f"%{safe_genre}%"))
            count_query = count_query.where(Track.genre.ilike(f"%{safe_genre}%"))
    
    # Get total count
    total = await db.scalar(count_query)
    
    # Apply sorting
    sort_column = getattr(Track, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    # Execute
    result = await db.execute(query)
    tracks = result.scalars().all()
    
    return TracksListResponse(
        items=[TrackResponse.model_validate(t) for t in tracks],
        total=total or 0,
        page=page,
        per_page=per_page,
    )


@router.get("/artists")
async def get_artists(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of unique artists (split by comma/feat/&) with images from Last.fm"""
    
    result = await db.execute(
        select(Track.artist)
        .where(Track.user_id == user.id)
        .where(Track.artist.isnot(None))
    )
    
    # Split artists and count
    artist_counts = {}
    for (artist_str,) in result.all():
        # Split by common separators: comma, feat, &, x, vs
        artists = re.split(r'\s*[,&]\s*|\s+(?:feat\.?|ft\.?|x|vs\.?)\s+', artist_str, flags=re.IGNORECASE)
        for artist in artists:
            artist = artist.strip()
            if artist:
                artist_counts[artist] = artist_counts.get(artist, 0) + 1
    
    # Sort by count descending
    sorted_artists = sorted(artist_counts.items(), key=lambda x: (-x[1], x[0]))
    
    return [{"artist": name, "count": count, "image_url": None} for name, count in sorted_artists]


async def fetch_artist_image(artist_name: str) -> Optional[str]:
    """Fetch artist image from Last.fm API"""
    if not settings.lastfm_api_key:
        return None
    
    # Check cache
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
                    # Get large or extralarge image
                    for img in reversed(images):
                        if img.get("#text") and img.get("size") in ["large", "extralarge", "mega"]:
                            image_url = img["#text"]
                            _artist_image_cache[cache_key] = image_url
                            return image_url
                    # Fallback to any available image
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
    """Get artist image URL - from Last.fm or fallback to top track cover"""
    # Try Last.fm first
    image_url = await fetch_artist_image(artist_name)
    
    # Check if it's a valid image (not Last.fm placeholder)
    if image_url and "2a96cbd8b46e442fc41c2b86b821562f" not in image_url:
        return {"artist": artist_name, "image_url": image_url}
    
    # Fallback: get cover from most played track by this artist
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
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of unique genres"""
    result = await db.execute(
        select(Track.genre, func.count(Track.id).label("count"))
        .where(Track.user_id == user.id)
        .where(Track.genre.isnot(None))
        .group_by(Track.genre)
        .order_by(func.count(Track.id).desc())
    )
    
    return [{"genre": row[0], "count": row[1]} for row in result.all()]


@router.get("/enrichment/status")
async def get_enrichment_status(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get enrichment status for user's tracks"""
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


@router.get("/history")
async def get_listening_history(
    limit: int = Query(50, ge=1, le=100),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get listening history (recently played tracks)"""
    result = await db.execute(
        select(Track)
        .where(Track.user_id == user.id)
        .where(Track.last_played_at.isnot(None))
        .order_by(Track.last_played_at.desc())
        .limit(limit)
    )
    
    tracks = result.scalars().all()
    return [TrackResponse.model_validate(t) for t in tracks]


@router.get("/liked")
async def get_liked_tracks(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all liked tracks"""
    result = await db.execute(
        select(Track)
        .where(Track.user_id == user.id)
        .where(Track.is_liked == True)
        .order_by(Track.liked_at.desc())
    )
    
    tracks = result.scalars().all()
    return [TrackResponse.model_validate(t) for t in tracks]


@router.post("/{track_id}/like")
async def like_track(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Like a track"""
    track = await db.scalar(
        select(Track).where(
            Track.id == track_id,
            Track.user_id == user.id
        )
    )
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    track.is_liked = True
    track.liked_at = datetime.utcnow()
    
    await db.commit()
    
    return {"status": "liked", "id": track_id, "is_liked": True}


@router.delete("/{track_id}/like")
async def unlike_track(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unlike a track"""
    track = await db.scalar(
        select(Track).where(
            Track.id == track_id,
            Track.user_id == user.id
        )
    )
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    track.is_liked = False
    track.liked_at = None
    
    await db.commit()
    
    return {"status": "unliked", "id": track_id, "is_liked": False}


@router.get("/{track_id}", response_model=TrackResponse)
async def get_track(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get single track by ID"""
    track = await db.scalar(
        select(Track).where(
            Track.id == track_id,
            Track.user_id == user.id
        )
    )
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    return TrackResponse.model_validate(track)


@router.put("/{track_id}", response_model=TrackResponse)
async def update_track(
    track_id: int,
    data: TrackUpdate,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update track metadata"""
    track = await db.scalar(
        select(Track).where(
            Track.id == track_id,
            Track.user_id == user.id
        )
    )
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(track, field, value)
    
    await db.commit()
    await db.refresh(track)
    
    return TrackResponse.model_validate(track)


@router.delete("/{track_id}")
async def delete_track(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete track from library"""
    track = await db.scalar(
        select(Track).where(
            Track.id == track_id,
            Track.user_id == user.id
        )
    )
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    await db.delete(track)
    await db.commit()
    
    return {"status": "deleted", "id": track_id}


@router.post("/{track_id}/mark-unavailable")
async def mark_track_unavailable(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a track as unavailable (file deleted from Telegram)"""
    track = await db.scalar(
        select(Track).where(
            Track.id == track_id,
            Track.user_id == user.id
        )
    )
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    track.is_unavailable = True
    await db.commit()
    
    return {"status": "marked_unavailable", "id": track_id}


@router.get("/unavailable/list")
async def get_unavailable_tracks(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all unavailable tracks"""
    result = await db.execute(
        select(Track)
        .where(Track.user_id == user.id)
        .where(Track.is_unavailable == True)
    )
    
    tracks = result.scalars().all()
    return [TrackResponse.model_validate(t) for t in tracks]


@router.delete("/unavailable/all")
async def delete_all_unavailable_tracks(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete all unavailable tracks"""
    from sqlalchemy import delete as sql_delete
    
    result = await db.execute(
        sql_delete(Track)
        .where(Track.user_id == user.id)
        .where(Track.is_unavailable == True)
    )
    
    await db.commit()
    
    return {"status": "deleted", "count": result.rowcount}

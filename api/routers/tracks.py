"""
TG Player API - Tracks Router
"""
import re
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

from .auth import get_current_user, TelegramUser


router = APIRouter()


def sanitize_input(value: str) -> str:
    """Sanitize input to prevent SQL injection"""
    if not value:
        return ""
    # Remove dangerous characters
    value = re.sub(r'[;\'"\\]', '', value)
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
    sort_by: str = Query("created_at", regex="^(created_at|title|artist|duration)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
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
            search_filter = or_(
                Track.title.ilike(f"%{safe_search}%"),
                Track.artist.ilike(f"%{safe_search}%"),
                Track.album.ilike(f"%{safe_search}%"),
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
    
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
    """Get list of unique artists (split by comma/feat/&)"""
    import re
    
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
    
    return [{"artist": name, "count": count} for name, count in sorted_artists]


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

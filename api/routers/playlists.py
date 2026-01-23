"""
TG Player API - Playlists Router
"""
from typing import Optional, List
from datetime import datetime
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import get_db
from shared.models import Playlist, PlaylistTrack, Track, UserLibrary

from .auth import get_current_user, TelegramUser
from .tracks import TrackResponse, track_to_response


router = APIRouter()


# Pydantic models
class PlaylistBase(BaseModel):
    name: str
    description: Optional[str] = None


class PlaylistCreate(PlaylistBase):
    pass


class PlaylistUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PlaylistResponse(PlaylistBase):
    id: int
    is_public: bool
    is_auto_album: bool = False
    is_auto_source: bool = False
    source_id: Optional[int] = None
    source_type: Optional[str] = None
    album_artist: Optional[str] = None  # Artist for album playlists
    cover_url: Optional[str] = None
    share_code: Optional[str]
    track_count: int = 0
    total_duration: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


class PlaylistWithTracksResponse(PlaylistResponse):
    tracks: List[TrackResponse]


class AddTrackRequest(BaseModel):
    track_id: int
    position: Optional[int] = None


@router.get("/sources", response_model=List[PlaylistResponse])
async def get_source_playlists(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's auto-generated source playlists (from forwarded messages)"""
    result = await db.execute(
        select(Playlist)
        .where(Playlist.user_id == user.id, Playlist.is_auto_source == True)
        .order_by(Playlist.created_at.desc())
    )
    playlists = result.scalars().all()
    
    response = []
    for playlist in playlists:
        count_result = await db.execute(
            select(func.count(PlaylistTrack.id))
            .where(PlaylistTrack.playlist_id == playlist.id)
        )
        track_count = count_result.scalar() or 0
        
        duration_result = await db.execute(
            select(func.sum(Track.duration))
            .join(PlaylistTrack, PlaylistTrack.track_id == Track.id)
            .where(PlaylistTrack.playlist_id == playlist.id)
        )
        total_duration = duration_result.scalar() or 0
        
        response.append(PlaylistResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            is_public=playlist.is_public,
            is_auto_album=playlist.is_auto_album,
            is_auto_source=playlist.is_auto_source,
            source_id=playlist.source_id,
            source_type=playlist.source_type,
            cover_url=playlist.cover_url,
            share_code=playlist.share_code,
            track_count=track_count,
            total_duration=total_duration,
            created_at=playlist.created_at,
        ))
    
    return response


@router.get("", response_model=List[PlaylistResponse])
async def get_playlists(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's playlists"""
    result = await db.execute(
        select(Playlist)
        .where(Playlist.user_id == user.id)
        .order_by(Playlist.created_at.desc())
    )
    playlists = result.scalars().all()
    
    # Get track counts and durations
    response = []
    for playlist in playlists:
        # Count tracks
        count_result = await db.execute(
            select(func.count(PlaylistTrack.id))
            .where(PlaylistTrack.playlist_id == playlist.id)
        )
        track_count = count_result.scalar() or 0
        
        # Sum duration
        duration_result = await db.execute(
            select(func.sum(Track.duration))
            .join(PlaylistTrack, PlaylistTrack.track_id == Track.id)
            .where(PlaylistTrack.playlist_id == playlist.id)
        )
        total_duration = duration_result.scalar() or 0
        
        response.append(PlaylistResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            is_public=playlist.is_public,
            is_auto_album=playlist.is_auto_album,
            is_auto_source=playlist.is_auto_source,
            source_id=playlist.source_id,
            source_type=playlist.source_type,
            cover_url=playlist.cover_url,
            share_code=playlist.share_code,
            track_count=track_count,
            total_duration=total_duration,
            created_at=playlist.created_at,
        ))
    
    return response


@router.post("", response_model=PlaylistResponse)
async def create_playlist(
    data: PlaylistCreate,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create new playlist"""
    playlist = Playlist(
        user_id=user.id,
        name=data.name,
        description=data.description,
    )
    
    db.add(playlist)
    await db.commit()
    await db.refresh(playlist)
    
    return PlaylistResponse(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        is_public=playlist.is_public,
        share_code=playlist.share_code,
        track_count=0,
        total_duration=0,
        created_at=playlist.created_at,
    )


@router.get("/{playlist_id}", response_model=PlaylistWithTracksResponse)
async def get_playlist(
    playlist_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get playlist with tracks"""
    result = await db.execute(
        select(Playlist)
        .options(
            selectinload(Playlist.track_associations)
            .selectinload(PlaylistTrack.track)
            .selectinload(Track.uploader)
        )
        .where(Playlist.id == playlist_id, Playlist.user_id == user.id)
    )
    playlist = result.scalar()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Get user's library entries for these tracks
    track_ids = [assoc.track.id for assoc in playlist.track_associations]
    lib_result = await db.execute(
        select(UserLibrary)
        .where(UserLibrary.user_id == user.id)
        .where(UserLibrary.track_id.in_(track_ids))
    )
    user_lib = {lib.track_id: lib for lib in lib_result.scalars().all()}
    
    tracks = [
        track_to_response(assoc.track, user_lib.get(assoc.track.id), user.id)
        for assoc in sorted(playlist.track_associations, key=lambda x: x.position)
    ]
    
    total_duration = sum(t.duration or 0 for t in tracks)
    
    return PlaylistWithTracksResponse(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        is_public=playlist.is_public,
        share_code=playlist.share_code,
        track_count=len(tracks),
        total_duration=total_duration,
        created_at=playlist.created_at,
        tracks=tracks,
    )


@router.put("/{playlist_id}", response_model=PlaylistResponse)
async def update_playlist(
    playlist_id: int,
    data: PlaylistUpdate,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update playlist"""
    playlist = await db.scalar(
        select(Playlist).where(
            Playlist.id == playlist_id,
            Playlist.user_id == user.id
        )
    )
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(playlist, field, value)
    
    await db.commit()
    await db.refresh(playlist)
    
    # Get counts
    count = await db.scalar(
        select(func.count(PlaylistTrack.id))
        .where(PlaylistTrack.playlist_id == playlist.id)
    )
    
    return PlaylistResponse(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        is_public=playlist.is_public,
        share_code=playlist.share_code,
        track_count=count or 0,
        total_duration=0,
        created_at=playlist.created_at,
    )


@router.delete("/{playlist_id}")
async def delete_playlist(
    playlist_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete playlist"""
    playlist = await db.scalar(
        select(Playlist).where(
            Playlist.id == playlist_id,
            Playlist.user_id == user.id
        )
    )
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    await db.delete(playlist)
    await db.commit()
    
    return {"status": "deleted", "id": playlist_id}


@router.post("/{playlist_id}/tracks")
async def add_track_to_playlist(
    playlist_id: int,
    data: AddTrackRequest,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add track to playlist (can add any public track)"""
    # Verify playlist exists and belongs to user
    playlist = await db.scalar(
        select(Playlist).where(
            Playlist.id == playlist_id,
            Playlist.user_id == user.id
        )
    )
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Verify track exists and is accessible (public or own)
    from sqlalchemy import or_
    track = await db.scalar(
        select(Track).where(
            Track.id == data.track_id,
            or_(
                Track.is_public == True,
                Track.user_id == user.id
            )
        )
    )
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found or is private")
    
    # Check if already in playlist
    existing = await db.scalar(
        select(PlaylistTrack).where(
            PlaylistTrack.playlist_id == playlist_id,
            PlaylistTrack.track_id == data.track_id
        )
    )
    
    if existing:
        raise HTTPException(status_code=400, detail="Track already in playlist")
    
    # Get next position
    if data.position is not None:
        position = data.position
    else:
        max_pos = await db.scalar(
            select(func.max(PlaylistTrack.position))
            .where(PlaylistTrack.playlist_id == playlist_id)
        )
        position = (max_pos or 0) + 1
    
    # Add track
    playlist_track = PlaylistTrack(
        playlist_id=playlist_id,
        track_id=data.track_id,
        position=position,
    )
    
    db.add(playlist_track)
    await db.commit()
    
    return {"status": "added", "playlist_id": playlist_id, "track_id": data.track_id}


@router.delete("/{playlist_id}/tracks/{track_id}")
async def remove_track_from_playlist(
    playlist_id: int,
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove track from playlist"""
    # Verify playlist belongs to user
    playlist = await db.scalar(
        select(Playlist).where(
            Playlist.id == playlist_id,
            Playlist.user_id == user.id
        )
    )
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Find and delete association
    assoc = await db.scalar(
        select(PlaylistTrack).where(
            PlaylistTrack.playlist_id == playlist_id,
            PlaylistTrack.track_id == track_id
        )
    )
    
    if not assoc:
        raise HTTPException(status_code=404, detail="Track not in playlist")
    
    await db.delete(assoc)
    await db.commit()
    
    return {"status": "removed", "playlist_id": playlist_id, "track_id": track_id}


@router.post("/{playlist_id}/share")
async def share_playlist(
    playlist_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate share code for playlist (placeholder for premium)"""
    playlist = await db.scalar(
        select(Playlist).where(
            Playlist.id == playlist_id,
            Playlist.user_id == user.id
        )
    )
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # TODO: Check premium status
    # For now, just generate code
    
    if not playlist.share_code:
        playlist.share_code = secrets.token_urlsafe(8)
        playlist.is_public = True
        await db.commit()
    
    return {
        "share_code": playlist.share_code,
        "share_url": f"https://t.me/your_bot?start=playlist_{playlist.share_code}"
    }


# ============ Auto-Albums ============

@router.get("/albums", response_model=List[PlaylistResponse])
async def get_albums(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's auto-generated album playlists"""
    result = await db.execute(
        select(Playlist)
        .where(
            Playlist.user_id == user.id,
            Playlist.is_auto_album == True
        )
        .order_by(Playlist.name)
    )
    playlists = result.scalars().all()
    
    # Deduplicate albums by name (case-insensitive)
    seen_albums = {}
    unique_playlists = []
    for playlist in playlists:
        # Use lowercase name as key for dedup
        key = playlist.name.lower().strip() if playlist.name else str(playlist.id)
        if key not in seen_albums:
            seen_albums[key] = playlist
            unique_playlists.append(playlist)
    
    response = []
    for playlist in unique_playlists:
        count_result = await db.execute(
            select(func.count(PlaylistTrack.id))
            .where(PlaylistTrack.playlist_id == playlist.id)
        )
        track_count = count_result.scalar() or 0
        
        duration_result = await db.execute(
            select(func.sum(Track.duration))
            .join(PlaylistTrack, PlaylistTrack.track_id == Track.id)
            .where(PlaylistTrack.playlist_id == playlist.id)
        )
        total_duration = duration_result.scalar() or 0
        
        response.append(PlaylistResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            is_public=playlist.is_public,
            is_auto_album=playlist.is_auto_album,
            is_auto_source=playlist.is_auto_source,
            source_id=playlist.source_id,
            source_type=playlist.source_type,
            album_artist=playlist.album_artist,
            cover_url=playlist.cover_url,
            share_code=playlist.share_code,
            track_count=track_count,
            total_duration=total_duration,
            created_at=playlist.created_at,
        ))
    
    return response


class AlbumCandidateResponse(BaseModel):
    artist: str
    album: str
    track_count: int
    total_duration: int
    cover_url: Optional[str] = None
    has_playlist: bool = False


@router.get("/albums/candidates", response_model=List[AlbumCandidateResponse])
async def get_album_candidates(
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get potential albums that can be auto-assembled"""
    # Import here to avoid circular imports
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from bot.services.albums import album_service
    
    candidates = await album_service.get_album_candidates(user.id)
    
    # Check which ones already have playlists
    response = []
    for c in candidates:
        existing = await album_service.check_existing_album_playlist(
            user.id, c["album"], c.get("deezer_album_id")
        )
        # Get all artists or fall back to single artist
        all_artists = c.get("all_artists", [c.get("artist", "Unknown")])
        if len(all_artists) > 2:
            artist_display = f"{all_artists[0]} и др."
        elif len(all_artists) == 2:
            artist_display = " & ".join(all_artists)
        else:
            artist_display = all_artists[0] if all_artists else "Unknown"
        
        response.append(AlbumCandidateResponse(
            artist=artist_display,
            album=c["album"],
            track_count=c["track_count"],
            total_duration=c["total_duration"],
            cover_url=c.get("cover_url"),
            has_playlist=existing is not None
        ))
    
    return response


class AssembleAlbumsResponse(BaseModel):
    created: int
    updated: int
    skipped: int
    albums: List[dict]


@router.post("/albums/assemble", response_model=AssembleAlbumsResponse)
async def assemble_albums(
    user: TelegramUser = Depends(get_current_user),
):
    """Manually trigger album assembly for user"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from bot.services.albums import album_service
    
    stats = await album_service.assemble_albums_for_user(user.id)
    
    return AssembleAlbumsResponse(
        created=stats["created"],
        updated=stats["updated"],
        skipped=stats["skipped"],
        albums=stats["albums"]
    )

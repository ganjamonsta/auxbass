"""
TG Player API v2 - Albums Router

Album-related endpoints.
Filters out singles (albums with <2 tracks) and shows full tracklist with missing tracks.
"""
import json
from typing import Optional, List
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc, asc, or_, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.database import get_db
from shared.models import (
    Track, Album, AlbumTrack, UserLibrary, TrackTag, TrackEnrichment
)
from shared.matching import (
    normalize_artist, normalize_title, fuzzy_match_title,
    normalize_album, fuzzy_match_artist, ARTIST_MATCH_THRESHOLD
)

from api.routers.auth import get_current_user
from api.utils.responses import streamable_track_filter, album_to_response, track_to_response
from api.schemas.albums import (
    AlbumResponse,
    AlbumDetailResponse,
    AlbumsListResponse,
    AlbumTracklistItem,
    AlbumResolveResponse,
)
from api.schemas.common import TelegramUser
from bot.services.albums import album_service


router = APIRouter(tags=["Albums"])

# Minimum tracks in user's library to show album (filters out singles)
MIN_USER_TRACKS_FOR_ALBUM = 2


async def get_albums_tags(
    db: AsyncSession,
    album_ids: list[int],
    limit_per_album: int = 4,
) -> dict[int, list[str]]:
    """
    Get top tags for a list of album IDs.
    Aggregates from TrackTag (user & Last.fm) and TrackEnrichment.genre of album tracks.
    Returns dict mapping album_id -> list of top tags.
    """
    if not album_ids:
        return {}

    tags_by_album: dict[int, list[str]] = defaultdict(list)
    seen_by_album: dict[int, set[str]] = defaultdict(set)

    # 1. Fetch top tags from TrackTag via AlbumTrack
    query = (
        select(AlbumTrack.album_id, TrackTag.tag, func.count(TrackTag.id).label("cnt"))
        .join(TrackTag, TrackTag.track_id == AlbumTrack.track_id)
        .where(AlbumTrack.album_id.in_(album_ids))
        .group_by(AlbumTrack.album_id, TrackTag.tag)
        .order_by(desc("cnt"))
    )
    result = await db.execute(query)
    for album_id, tag, _ in result.all():
        if not album_id or not tag:
            continue
        tag_lower = tag.lower().strip()
        if tag_lower and tag_lower not in seen_by_album[album_id]:
            if len(tags_by_album[album_id]) < limit_per_album:
                seen_by_album[album_id].add(tag_lower)
                tags_by_album[album_id].append(tag)

    # 2. Check TrackEnrichment.genre for albums with room
    missing = [aid for aid in album_ids if len(tags_by_album[aid]) < limit_per_album]
    if missing:
        genre_query = (
            select(AlbumTrack.album_id, TrackEnrichment.genre, func.count(TrackEnrichment.id).label("cnt"))
            .join(TrackEnrichment, TrackEnrichment.track_id == AlbumTrack.track_id)
            .where(AlbumTrack.album_id.in_(missing))
            .where(TrackEnrichment.genre.is_not(None))
            .where(TrackEnrichment.genre != "")
            .group_by(AlbumTrack.album_id, TrackEnrichment.genre)
            .order_by(desc("cnt"))
        )
        genre_result = await db.execute(genre_query)
        for album_id, genre, _ in genre_result.all():
            if not album_id or not genre:
                continue
            g_lower = genre.lower().strip()
            if g_lower and g_lower not in seen_by_album[album_id]:
                if len(tags_by_album[album_id]) < limit_per_album:
                    seen_by_album[album_id].add(g_lower)
                    tags_by_album[album_id].append(genre.lower())

    return dict(tags_by_album)


@router.get("", response_model=AlbumsListResponse)
async def get_my_albums(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    artist: Optional[str] = None,
    sort_by: str = Query("name", pattern="^(name|artist|release_date|track_count)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    min_tracks: int = Query(MIN_USER_TRACKS_FOR_ALBUM, ge=1, description="Minimum tracks in library to show album"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get albums from user's library.
    
    Only returns albums that contain at least min_tracks tracks from user's library.
    Default min_tracks=2 filters out singles.
    """
    # Subquery: album IDs with track count >= min_tracks
    album_track_counts = (
        select(
            AlbumTrack.album_id,
            func.count(AlbumTrack.track_id).label("track_count")
        )
        .join(UserLibrary, UserLibrary.track_id == AlbumTrack.track_id)
        .where(UserLibrary.user_id == user.id)
        .group_by(AlbumTrack.album_id)
        .having(func.count(AlbumTrack.track_id) >= min_tracks)
        .subquery()
    )
    
    # Base query - join with filtered album IDs
    query = (
        select(Album, album_track_counts.c.track_count)
        .join(album_track_counts, Album.id == album_track_counts.c.album_id)
    )
    count_query = (
        select(func.count(Album.id))
        .join(album_track_counts, Album.id == album_track_counts.c.album_id)
    )
    
    # Apply search
    if search:
        search_clean = search.lstrip('#').strip()
        search_term = f"%{search_clean}%"

        tag_album_ids = (
            select(AlbumTrack.album_id)
            .join(TrackTag, TrackTag.track_id == AlbumTrack.track_id)
            .where(TrackTag.tag.ilike(search_term))
        )
        genre_album_ids = (
            select(AlbumTrack.album_id)
            .join(TrackEnrichment, TrackEnrichment.track_id == AlbumTrack.track_id)
            .where(or_(
                TrackEnrichment.genre.ilike(search_term),
                func.cast(TrackEnrichment.tags, String).ilike(search_term)
            ))
        )

        search_filter = or_(
            Album.name.ilike(search_term),
            Album.artist.ilike(search_term),
            Album.id.in_(tag_album_ids),
            Album.id.in_(genre_album_ids),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    
    # Apply artist filter
    if artist:
        query = query.where(Album.artist.ilike(artist))
        count_query = count_query.where(Album.artist.ilike(artist))
    
    # Count total
    total = await db.scalar(count_query) or 0
    
    # Sorting - add secondary sort by ID for stable pagination
    if sort_by == "artist":
        sort_column = Album.artist
    elif sort_by == "release_date":
        sort_column = Album.release_date
    elif sort_by == "track_count":
        sort_column = album_track_counts.c.track_count
    else:
        sort_column = Album.name
    
    if sort_order == "desc":
        query = query.order_by(desc(sort_column).nullslast(), desc(Album.id))
    else:
        query = query.order_by(asc(sort_column).nullsfirst(), asc(Album.id))
    
    # Pagination
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    # Build response - track counts and tags are included
    album_ids = [album.id for album, _ in rows]
    album_tags_map = await get_albums_tags(db, album_ids)
    items = [
        album_to_response(album, track_count, tags=album_tags_map.get(album.id))
        for album, track_count in rows
    ]
    
    return AlbumsListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
    )


# ============== Global Library ==============

@router.get("/global", response_model=AlbumsListResponse)
async def get_global_albums(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    artist: Optional[str] = None,
    sort_by: str = Query("name", pattern="^(name|artist|release_date|track_count)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    min_tracks: int = Query(1, ge=1, description="Minimum tracks to show album"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get albums from global public library.
    
    Shows albums that have at least min_tracks public tracks.
    """
    # Subquery: album IDs with public track count >= min_tracks
    album_track_counts = (
        select(
            AlbumTrack.album_id,
            func.count(AlbumTrack.track_id).label("track_count")
        )
        .join(Track, Track.id == AlbumTrack.track_id)
        .where(Track.is_public == True)
        .where(Track.is_unavailable == False)
        .group_by(AlbumTrack.album_id)
        .having(func.count(AlbumTrack.track_id) >= min_tracks)
        .subquery()
    )
    
    # Base query - join with filtered album IDs
    query = (
        select(Album, album_track_counts.c.track_count)
        .join(album_track_counts, Album.id == album_track_counts.c.album_id)
    )
    count_query = (
        select(func.count(Album.id))
        .join(album_track_counts, Album.id == album_track_counts.c.album_id)
    )
    
    # Apply search
    if search:
        search_clean = search.lstrip('#').strip()
        search_term = f"%{search_clean}%"

        tag_album_ids = (
            select(AlbumTrack.album_id)
            .join(TrackTag, TrackTag.track_id == AlbumTrack.track_id)
            .where(TrackTag.tag.ilike(search_term))
        )
        genre_album_ids = (
            select(AlbumTrack.album_id)
            .join(TrackEnrichment, TrackEnrichment.track_id == AlbumTrack.track_id)
            .where(or_(
                TrackEnrichment.genre.ilike(search_term),
                func.cast(TrackEnrichment.tags, String).ilike(search_term)
            ))
        )

        search_filter = or_(
            Album.name.ilike(search_term),
            Album.artist.ilike(search_term),
            Album.id.in_(tag_album_ids),
            Album.id.in_(genre_album_ids),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    
    # Apply artist filter
    if artist:
        query = query.where(Album.artist.ilike(artist))
        count_query = count_query.where(Album.artist.ilike(artist))
    
    # Count total
    total = await db.scalar(count_query) or 0
    
    # Sorting - add secondary sort by ID for stable pagination
    if sort_by == "artist":
        sort_column = Album.artist
    elif sort_by == "release_date":
        sort_column = Album.release_date
    elif sort_by == "track_count":
        sort_column = album_track_counts.c.track_count
    else:
        sort_column = Album.name
    
    if sort_order == "desc":
        query = query.order_by(desc(sort_column).nullslast(), desc(Album.id))
    else:
        query = query.order_by(asc(sort_column).nullsfirst(), asc(Album.id))
    
    # Pagination
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    # Build response
    album_ids = [album.id for album, _ in rows]
    album_tags_map = await get_albums_tags(db, album_ids)
    items = [
        album_to_response(album, track_count, tags=album_tags_map.get(album.id))
        for album, track_count in rows
    ]
    
    return AlbumsListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/resolve", response_model=AlbumResolveResponse)
async def resolve_album(
    track_id: Optional[int] = Query(None, description="Track ID to resolve album for"),
    album_name: Optional[str] = Query(None, description="Album name"),
    artist: Optional[str] = Query(None, description="Artist name"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Resolve or dynamically create an album for a track or by album name/artist.
    Ensures album navigation always succeeds even if the album was not pre-created or linked.
    """
    if not isinstance(track_id, int):
        track_id = None
    if not isinstance(album_name, str):
        album_name = None
    if not isinstance(artist, str):
        artist = None

    target_track = None
    if track_id:
        # 1. Check if track is already linked to an album
        res = await db.execute(
            select(AlbumTrack.album_id, Album.name, Album.artist)
            .join(Album, Album.id == AlbumTrack.album_id)
            .where(AlbumTrack.track_id == track_id)
        )
        row = res.first()
        if row:
            return AlbumResolveResponse(album_id=row[0], name=row[1], artist=row[2])

        # 2. Try auto_assign_album_from_enrichment
        target_track = await db.scalar(
            select(Track)
            .options(selectinload(Track.enrichment))
            .where(Track.id == track_id)
        )
        if target_track:
            assigned_id = await album_service.auto_assign_album_from_enrichment(track_id)
            if assigned_id:
                album = await db.get(Album, assigned_id)
                if album:
                    return AlbumResolveResponse(album_id=album.id, name=album.name, artist=album.artist)

            if not album_name and target_track.enrichment and target_track.enrichment.album_name:
                album_name = target_track.enrichment.album_name
            if not artist:
                artist = target_track.artist

    if not album_name or not album_name.strip():
        raise HTTPException(status_code=404, detail="Album name not specified or found")

    album_name = album_name.strip()
    norm_album = normalize_album(album_name)

    # 3. Look up existing album by Deezer album ID if available on track
    if target_track and target_track.enrichment and target_track.enrichment.deezer_album_id:
        album_by_dz = await db.scalar(
            select(Album).where(Album.deezer_album_id == target_track.enrichment.deezer_album_id)
        )
        if album_by_dz:
            if track_id:
                await album_service.assign_track_to_album(track_id, album_by_dz.id)
            return AlbumResolveResponse(album_id=album_by_dz.id, name=album_by_dz.name, artist=album_by_dz.artist)

    # 4. Search existing album by normalized name and artist
    query = select(Album).where(Album.normalized_name == norm_album)
    if artist:
        norm_artist = normalize_artist(artist)
        query = query.where(Album.normalized_artist == norm_artist)

    matched_album = await db.scalar(query)

    # 5. If not exact match, try fuzzy matching artist among albums with same normalized_name
    if not matched_album and artist:
        cands = (await db.scalars(select(Album).where(Album.normalized_name == norm_album))).all()
        for cand in cands:
            if fuzzy_match_artist(artist, cand.artist) >= ARTIST_MATCH_THRESHOLD:
                matched_album = cand
                break

    if matched_album:
        if track_id:
            await album_service.assign_track_to_album(track_id, matched_album.id)
        return AlbumResolveResponse(album_id=matched_album.id, name=matched_album.name, artist=matched_album.artist)

    # 6. Create album via album_service
    created_id = await album_service.find_or_create_album(
        album_name=album_name,
        artist_name=artist or "Неизвестный исполнитель"
    )
    if created_id:
        if track_id:
            await album_service.assign_track_to_album(track_id, created_id)
        created_album = await db.get(Album, created_id)
        if created_album:
            return AlbumResolveResponse(album_id=created_album.id, name=created_album.name, artist=created_album.artist)

    raise HTTPException(status_code=404, detail="Album could not be resolved or created")


@router.get("/{album_id}", response_model=AlbumDetailResponse)
async def get_album(
    album_id: int,
    scope: str = Query("library", pattern="^(library|global)$"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get album details with tracks.
    
    scope=library: only user's library tracks
    scope=global: all public tracks from this album
    """
    album = await db.get(Album, album_id)
    
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    

    
    if scope == "global":
        # Get all public tracks from this album
        result = await db.execute(
            select(Track, AlbumTrack)
            .join(AlbumTrack, AlbumTrack.track_id == Track.id)
            .where(
                AlbumTrack.album_id == album_id,
                Track.is_public == True,
                Track.is_unavailable == False
            )
            .options(
                selectinload(Track.enrichment),
                selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
            )
            .order_by(AlbumTrack.track_number.asc().nullslast())
        )
        rows = result.unique().all()
        
        # Get user's library to mark which tracks are in library
        user_lib_result = await db.execute(
            select(UserLibrary.track_id)
            .where(UserLibrary.user_id == user.id)
        )
        user_library_ids = set(row[0] for row in user_lib_result.all())
        
        tracks = [
            track_to_response(track, in_library=track.id in user_library_ids)
            for track, at in rows
        ]
        
        # Build full tracklist for global scope
        full_tracklist = None
        if album.full_tracklist:
            try:
                tracklist_data = json.loads(album.full_tracklist)
                
                # Create lookup by track_number and by normalized title
                tracks_by_pos = {}
                tracks_by_title = {}
                for track, at in rows:
                    if at.track_number and at.track_number > 0:
                        tracks_by_pos[at.track_number] = track
                    norm_title = normalize_title(track.title or "")
                    tracks_by_title[norm_title] = track
                
                full_tracklist = []
                for item in tracklist_data:
                    item_title = item.get("title", "")
                    norm_item_title = normalize_title(item_title)
                    item_num = item.get("track_number", 0)
                    
                    matched_track = None
                    if item_num and item_num in tracks_by_pos:
                        matched_track = tracks_by_pos[item_num]
                    elif norm_item_title in tracks_by_title:
                        matched_track = tracks_by_title[norm_item_title]
                    else:
                        best_match_score = 0.0
                        for norm_title, track in tracks_by_title.items():
                            score = fuzzy_match_title(item_title, track.title or "")
                            if score >= 0.85 and score > best_match_score:
                                best_match_score = score
                                matched_track = track
                    
                    effective_duration = (matched_track.duration if matched_track and matched_track.duration else None) or item.get("duration", 0)
                    
                    tracklist_item = AlbumTracklistItem(
                        track_number=item.get("track_number", 0),
                        title=item_title,
                        artist=item.get("artist", ""),
                        duration=effective_duration,
                        deezer_id=item.get("deezer_id"),
                        in_library=matched_track.id in user_library_ids if matched_track else False,
                        track_id=matched_track.id if matched_track else None,
                        track=track_to_response(matched_track, in_library=matched_track.id in user_library_ids) if matched_track else None,
                    )
                    full_tracklist.append(tracklist_item)
            except (json.JSONDecodeError, Exception):
                full_tracklist = None
    else:
        # Library scope: show all album tracks, mark which ones are in user's library
        # First, get ALL tracks from this album (not just user's library)
        all_album_tracks_result = await db.execute(
            select(Track, AlbumTrack)
            .join(AlbumTrack, AlbumTrack.track_id == Track.id)
            .where(
                AlbumTrack.album_id == album_id,
                Track.is_public == True,
                Track.is_unavailable == False
            )
            .options(
                selectinload(Track.enrichment),
                selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
            )
            .order_by(AlbumTrack.track_number.asc().nullslast())
        )
        all_album_rows = all_album_tracks_result.unique().all()
        
        # Get user's library entries for these tracks
        track_ids_in_album = [track.id for track, at in all_album_rows]
        user_lib_result = await db.execute(
            select(UserLibrary)
            .where(
                UserLibrary.user_id == user.id,
                UserLibrary.track_id.in_(track_ids_in_album) if track_ids_in_album else False
            )
        )
        user_lib_entries = {lib.track_id: lib for lib in user_lib_result.scalars().all()}
        
        # Build tracks list - only tracks in user's library for compatibility
        user_tracks = [
            (track, user_lib_entries.get(track.id), at.track_number) 
            for track, at in all_album_rows 
            if track.id in user_lib_entries
        ]
        tracks = [track_to_response(track, lib_entry) for track, lib_entry, _ in user_tracks]
        
        # Build full tracklist with ALL album tracks (playable from global), mark in_library status
        full_tracklist = None
        if album.full_tracklist:
            try:
                tracklist_data = json.loads(album.full_tracklist)
                
                # Use ALL album tracks for matching: lookup by position and normalized title
                all_tracks_by_pos = {}
                all_tracks_by_title = {}
                for track, at in all_album_rows:
                    if at.track_number and at.track_number > 0:
                        all_tracks_by_pos[at.track_number] = track
                    norm_title = normalize_title(track.title or "")
                    all_tracks_by_title[norm_title] = track
                
                full_tracklist = []
                for item in tracklist_data:
                    item_title = item.get("title", "")
                    norm_item_title = normalize_title(item_title)
                    item_num = item.get("track_number", 0)
                    
                    matched_track = None
                    if item_num and item_num in all_tracks_by_pos:
                        matched_track = all_tracks_by_pos[item_num]
                    elif norm_item_title in all_tracks_by_title:
                        matched_track = all_tracks_by_title[norm_item_title]
                    else:
                        best_match_score = 0.0
                        for norm_title, track in all_tracks_by_title.items():
                            score = fuzzy_match_title(item_title, track.title or "")
                            if score >= 0.85 and score > best_match_score:
                                best_match_score = score
                                matched_track = track
                    
                    # Check if matched track is in user's library
                    in_library = matched_track.id in user_lib_entries if matched_track else False
                    matched_lib = user_lib_entries.get(matched_track.id) if matched_track else None
                    
                    # For tracks in library, use track_to_response with or without library_entry
                    track_response = None
                    if matched_track:
                        if matched_lib:
                            track_response = track_to_response(matched_track, matched_lib)
                        else:
                            track_response = track_to_response(matched_track, in_library=False)
                    
                    effective_duration = (matched_track.duration if matched_track and matched_track.duration else None) or item.get("duration", 0)
                    
                    tracklist_item = AlbumTracklistItem(
                        track_number=item.get("track_number", 0),
                        title=item_title,
                        artist=item.get("artist", ""),
                        duration=effective_duration,
                        deezer_id=item.get("deezer_id"),
                        in_library=in_library,
                        track_id=matched_track.id if matched_track else None,
                        track=track_response,
                    )
                    full_tracklist.append(tracklist_item)
            except (json.JSONDecodeError, Exception):
                full_tracklist = None
    
    # Collect tags from album tracks (aggregate unique tags from enriched tracks)
    album_tags = None
    try:
        seen_tags = set()
        collected_tags = []
        # Get from all album tracks
        for track, at in (all_album_rows if scope == "library" else rows):
            enrichment = track.__dict__.get('enrichment')
            if enrichment and enrichment.tags:
                for tag in enrichment.tags:
                    tag_lower = tag.lower()
                    if tag_lower not in seen_tags:
                        seen_tags.add(tag_lower)
                        collected_tags.append(tag)
                        if len(collected_tags) >= 5:
                            break
            if len(collected_tags) >= 5:
                break
        if collected_tags:
            album_tags = collected_tags
    except Exception:
        album_tags = None

    if not album_tags:
        db_tags = await get_albums_tags(db, [album.id], limit_per_album=5)
        album_tags = db_tags.get(album.id) or None
    
    # Calculate track_count: count unique album tracks present in the response
    if full_tracklist:
        actual_track_count = sum(1 for it in full_tracklist if it.track)
    else:
        actual_track_count = len(set(t.id for t in tracks))
        if album.total_tracks and actual_track_count > album.total_tracks:
            actual_track_count = album.total_tracks
            
    return AlbumDetailResponse(
        id=album.id,
        name=album.name,
        artist=album.artist,
        cover_url=album.cover_url,
        release_date=album.release_date,
        track_count=actual_track_count,
        total_tracks=album.total_tracks,
        deezer_album_id=album.deezer_album_id,
        has_full_tracklist=bool(album.full_tracklist),
        tags=album_tags,
        tracks=tracks,
        full_tracklist=full_tracklist,
    )


@router.get("/by-artist/{artist_name}", response_model=List[AlbumResponse])
async def get_albums_by_artist(
    artist_name: str,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all albums by a specific artist in user's library"""
    artist_lower = artist_name.lower()
    
    # Albums by this artist that have tracks in user's library
    user_album_ids = (
        select(AlbumTrack.album_id)
        .distinct()
        .join(UserLibrary, UserLibrary.track_id == AlbumTrack.track_id)
        .where(UserLibrary.user_id == user.id)
        .subquery()
    )
    
    result = await db.execute(
        select(Album)
        .where(
            Album.id.in_(select(user_album_ids)),
            func.lower(Album.artist) == artist_lower
        )
        .order_by(Album.release_date.desc().nullslast())
    )
    albums = result.scalars().all()
    
    return [album_to_response(album) for album in albums]


@router.get("/{album_id}/ids")
async def get_album_track_ids(
    album_id: int,
    shuffle: bool = False,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all track IDs for an album.
    
    Lightweight endpoint for shuffle - returns only IDs.
    """
    album = await db.get(Album, album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    query = (
        select(Track.id)
        .join(AlbumTrack, AlbumTrack.track_id == Track.id)
        .join(UserLibrary, UserLibrary.track_id == Track.id)
        .where(
            AlbumTrack.album_id == album_id,
            UserLibrary.user_id == user.id,
            UserLibrary.is_disliked == False,
        )
        .where(streamable_track_filter())
    )
    
    if shuffle:
        query = query.order_by(func.random())
    else:
        query = query.order_by(AlbumTrack.track_number.asc().nullslast())
    
    result = await db.execute(query)
    track_ids = result.scalars().all()
    
    return {"ids": track_ids, "total": len(track_ids)}


@router.post("/{album_id}/find-track")
async def find_missing_track(
    album_id: int,
    title: str = Query(..., description="Track title to search for"),
    artist: Optional[str] = Query(None, description="Artist name (optional)"),
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Search for a missing track in the global library.
    
    When user clicks "+" on a missing album track:
    1. First search in global tracks table
    2. If found, return track info so user can add to library
    3. If not found, return instructions to send file to bot
    
    Returns:
        found: bool - whether track was found
        track: optional track data if found in global library
        message: instructions for user
    """
    album = await db.get(Album, album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    # Use album's artist if not provided
    search_artist = artist or album.artist
    
    # Normalize for search
    norm_title = normalize_title(title)
    norm_artist = normalize_artist(search_artist) if search_artist else None
    
    # Search in global tracks
    query = select(Track).options(
        selectinload(Track.enrichment),
        selectinload(Track.album_tracks).selectinload(AlbumTrack.album),
    )
    
    # Try to find by normalized title match
    result = await db.execute(query)
    all_tracks = result.scalars().all()
    
    # Find best match
    best_match = None
    best_score = 0.0
    
    for track in all_tracks:
        title_score = fuzzy_match_title(title, track.title or "")
        if title_score < 0.7:
            continue
        
        # Check artist match if we have one
        artist_score = 1.0
        if norm_artist and track.artist:
            from shared.matching import fuzzy_match_artist
            artist_score = fuzzy_match_artist(search_artist, track.artist)
        
        combined = (title_score * 0.6) + (artist_score * 0.4)
        if combined > best_score:
            best_score = combined
            best_match = track
    
    if best_match and best_score >= 0.6:
        # Check if already in user's library
        in_library = await db.scalar(
            select(UserLibrary.id)
            .where(
                UserLibrary.user_id == user.id,
                UserLibrary.track_id == best_match.id
            )
        )
        

        
        return {
            "found": True,
            "in_library": in_library is not None,
            "track_id": best_match.id,
            "track": track_to_response(best_match, None),
            "message": "Трек найден в библиотеке!" if in_library else "Трек найден! Добавить в библиотеку?"
        }
    
    # Not found - suggest sending to bot
    return {
        "found": False,
        "in_library": False,
        "track_id": None,
        "track": None,
        "message": f"Трек не найден. Отправь файл «{title}» боту, чтобы добавить его."
    }


@router.post("/{album_id}/add-track/{track_id}")
async def add_track_to_album_and_library(
    album_id: int,
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add an existing track to user's library and associate with album.
    
    Used when user finds a missing track in global library and wants to add it.
    """
    album = await db.get(Album, album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    
    track = await db.get(Track, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Check if already in user's library
    existing_lib = await db.scalar(
        select(UserLibrary.id)
        .where(
            UserLibrary.user_id == user.id,
            UserLibrary.track_id == track_id
        )
    )
    
    if not existing_lib:
        # Add to user's library
        from shared.models import LibrarySource
        lib_entry = UserLibrary(
            user_id=user.id,
            track_id=track_id,
            source=LibrarySource.ADDED,  # User explicitly added
        )
        db.add(lib_entry)
    
    # Check if track is already in album
    existing_album_track = await db.scalar(
        select(AlbumTrack.id)
        .where(
            AlbumTrack.album_id == album_id,
            AlbumTrack.track_id == track_id
        )
    )
    
    if not existing_album_track:
        # Determine track number from enrichment or tracklist
        track_number = 0
        if track.enrichment and track.enrichment.track_number:
            track_number = track.enrichment.track_number
        
        album_track = AlbumTrack(
            album_id=album_id,
            track_id=track_id,
            track_number=track_number,
        )
        db.add(album_track)
    
    await db.commit()
    
    return {
        "success": True,
        "message": "Трек добавлен в библиотеку и альбом!",
        "added_to_library": not existing_lib,
        "added_to_album": not existing_album_track,
    }

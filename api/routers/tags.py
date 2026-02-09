"""
TG Player API v2 - Tags Router

User-generated tags with voting/endorsement system.
Tags can be added by users or imported from Last.fm enrichment.
Users can vote (endorse) tags to confirm their relevance.
"""
import logging
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.database import get_db
from shared.models import (
    Track, TrackTag, TrackTagVote, UserLibrary, TagSource, utcnow
)
from api.routers.auth import get_current_user
from api.schemas.common import TelegramUser
from api.schemas.tags import (
    TagInfo, TrackTagsResponse, TagCreate, TagVoteResponse, GlobalTagInfo
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Tags"])

# ============== Constants ==============
MAX_TAGS_PER_TRACK = 15
MAX_TAG_LENGTH = 50
MIN_TAG_LENGTH = 2
TAG_PATTERN = re.compile(r'^[a-zA-Zа-яА-ЯёЁ0-9\s\-&/]+$')  # Letters, digits, spaces, hyphens, &, /


def normalize_tag(tag: str) -> str:
    """Normalize a tag string: lowercase, strip, collapse whitespace."""
    tag = tag.strip().lower()
    tag = re.sub(r'\s+', ' ', tag)
    return tag[:MAX_TAG_LENGTH]


# ============== Get Tags for Track ==============

@router.get("/{track_id}/tags", response_model=TrackTagsResponse)
async def get_track_tags(
    track_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all tags for a track with vote counts and user's vote status.
    """
    # Verify track exists
    track = await db.get(Track, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Get tags with vote counts and user's vote status
    query = (
        select(
            TrackTag,
            func.count(TrackTagVote.id).label("vote_count"),
            func.count(
                func.nullif(TrackTagVote.user_id != user.id, True)
            ).label("voted_by_me"),
        )
        .outerjoin(TrackTagVote, TrackTagVote.track_tag_id == TrackTag.id)
        .where(TrackTag.track_id == track_id)
        .group_by(TrackTag.id)
        .order_by(func.count(TrackTagVote.id).desc(), TrackTag.created_at.asc())
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    tags = []
    for track_tag, vote_count, voted_by_me in rows:
        tags.append(TagInfo(
            id=track_tag.id,
            tag=track_tag.tag,
            source=track_tag.source.value if isinstance(track_tag.source, TagSource) else track_tag.source,
            vote_count=vote_count,
            voted_by_me=voted_by_me > 0,
        ))
    
    return TrackTagsResponse(track_id=track_id, tags=tags)


# ============== Add Tag ==============

@router.post("/{track_id}/tags", response_model=TagInfo)
async def add_tag(
    track_id: int,
    body: TagCreate,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a new user tag to a track. Auto-votes for it.
    """
    # Verify track exists
    track = await db.get(Track, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Normalize tag
    tag_text = normalize_tag(body.tag)
    
    # Validate
    if len(tag_text) < MIN_TAG_LENGTH:
        raise HTTPException(status_code=400, detail=f"Тег слишком короткий (мин. {MIN_TAG_LENGTH} символа)")
    
    if not TAG_PATTERN.match(tag_text):
        raise HTTPException(status_code=400, detail="Тег содержит недопустимые символы")
    
    # Check if tag already exists for this track
    existing = await db.execute(
        select(TrackTag).where(TrackTag.track_id == track_id, TrackTag.tag == tag_text)
    )
    existing_tag = existing.scalar_one_or_none()
    
    if existing_tag:
        # Tag exists — just vote for it instead
        vote_exists = await db.execute(
            select(TrackTagVote).where(
                TrackTagVote.track_tag_id == existing_tag.id,
                TrackTagVote.user_id == user.id,
            )
        )
        if not vote_exists.scalar_one_or_none():
            vote = TrackTagVote(track_tag_id=existing_tag.id, user_id=user.id)
            db.add(vote)
            await db.commit()
        
        # Return current state
        vote_count = await db.execute(
            select(func.count(TrackTagVote.id)).where(TrackTagVote.track_tag_id == existing_tag.id)
        )
        return TagInfo(
            id=existing_tag.id,
            tag=existing_tag.tag,
            source=existing_tag.source.value if isinstance(existing_tag.source, TagSource) else existing_tag.source,
            vote_count=vote_count.scalar() or 0,
            voted_by_me=True,
        )
    
    # Check max tags limit
    tag_count = await db.execute(
        select(func.count(TrackTag.id)).where(TrackTag.track_id == track_id)
    )
    if (tag_count.scalar() or 0) >= MAX_TAGS_PER_TRACK:
        raise HTTPException(status_code=400, detail=f"Максимум {MAX_TAGS_PER_TRACK} тегов на трек")
    
    # Create new tag
    new_tag = TrackTag(
        track_id=track_id,
        tag=tag_text,
        source=TagSource.USER,
        created_by=user.id,
    )
    db.add(new_tag)
    await db.flush()
    
    # Auto-vote for own tag
    vote = TrackTagVote(track_tag_id=new_tag.id, user_id=user.id)
    db.add(vote)
    await db.commit()
    
    logger.info(f"User {user.id} added tag '{tag_text}' to track {track_id}")
    
    return TagInfo(
        id=new_tag.id,
        tag=new_tag.tag,
        source=new_tag.source.value,
        vote_count=1,
        voted_by_me=True,
    )


# ============== Vote / Unvote ==============

@router.post("/{track_id}/tags/{tag_id}/vote", response_model=TagVoteResponse)
async def vote_tag(
    track_id: int,
    tag_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Vote (endorse) a tag. Each user can vote once per tag.
    """
    # Verify tag exists and belongs to the track
    tag = await db.execute(
        select(TrackTag).where(TrackTag.id == tag_id, TrackTag.track_id == track_id)
    )
    track_tag = tag.scalar_one_or_none()
    if not track_tag:
        raise HTTPException(status_code=404, detail="Тег не найден")
    
    # Check if already voted
    existing_vote = await db.execute(
        select(TrackTagVote).where(
            TrackTagVote.track_tag_id == tag_id,
            TrackTagVote.user_id == user.id,
        )
    )
    if not existing_vote.scalar_one_or_none():
        vote = TrackTagVote(track_tag_id=tag_id, user_id=user.id)
        db.add(vote)
        await db.commit()
    
    # Get updated vote count
    vote_count = await db.execute(
        select(func.count(TrackTagVote.id)).where(TrackTagVote.track_tag_id == tag_id)
    )
    
    return TagVoteResponse(
        tag_id=tag_id,
        tag=track_tag.tag,
        vote_count=vote_count.scalar() or 0,
        voted_by_me=True,
    )


@router.delete("/{track_id}/tags/{tag_id}/vote", response_model=TagVoteResponse)
async def unvote_tag(
    track_id: int,
    tag_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove vote from a tag.
    """
    # Verify tag exists and belongs to the track
    tag = await db.execute(
        select(TrackTag).where(TrackTag.id == tag_id, TrackTag.track_id == track_id)
    )
    track_tag = tag.scalar_one_or_none()
    if not track_tag:
        raise HTTPException(status_code=404, detail="Тег не найден")
    
    # Remove vote if exists
    await db.execute(
        delete(TrackTagVote).where(
            TrackTagVote.track_tag_id == tag_id,
            TrackTagVote.user_id == user.id,
        )
    )
    await db.commit()
    
    # Get updated vote count
    vote_count = await db.execute(
        select(func.count(TrackTagVote.id)).where(TrackTagVote.track_tag_id == tag_id)
    )
    
    return TagVoteResponse(
        tag_id=tag_id,
        tag=track_tag.tag,
        vote_count=vote_count.scalar() or 0,
        voted_by_me=False,
    )


# ============== Delete Tag ==============

@router.delete("/{track_id}/tags/{tag_id}")
async def delete_tag(
    track_id: int,
    tag_id: int,
    user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a tag. Only the creator of a user-tag can delete it.
    Enrichment tags cannot be deleted by users.
    """
    tag = await db.execute(
        select(TrackTag).where(TrackTag.id == tag_id, TrackTag.track_id == track_id)
    )
    track_tag = tag.scalar_one_or_none()
    if not track_tag:
        raise HTTPException(status_code=404, detail="Тег не найден")
    
    # Only allow deleting user-created tags by their creator
    source = track_tag.source.value if isinstance(track_tag.source, TagSource) else track_tag.source
    if source == "enrichment":
        raise HTTPException(status_code=403, detail="Нельзя удалить импортированный тег")
    
    if track_tag.created_by != user.id:
        raise HTTPException(status_code=403, detail="Можно удалять только свои теги")
    
    await db.delete(track_tag)
    await db.commit()
    
    return {"status": "ok", "message": "Тег удалён"}

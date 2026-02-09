"""
TG Player API v2 - Tag Schemas
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class TagInfo(BaseModel):
    """Tag with vote info (returned in track responses)"""
    id: int
    tag: str
    source: str  # 'enrichment' or 'user'
    vote_count: int = 0
    voted_by_me: bool = False

    class Config:
        from_attributes = True


class TrackTagsResponse(BaseModel):
    """Tags for a specific track"""
    track_id: int
    tags: List[TagInfo]


class TagCreate(BaseModel):
    """Create a new tag on a track"""
    tag: str  # Will be normalized (lowercase, trimmed, max 50 chars)


class TagVoteResponse(BaseModel):
    """Response after voting/unvoting"""
    tag_id: int
    tag: str
    vote_count: int
    voted_by_me: bool


class GlobalTagInfo(BaseModel):
    """Tag with aggregate stats (for tag listing endpoints)"""
    name: str
    track_count: int
    total_votes: int = 0

"""
TG Player Bot - User Session State
Manages temporary state like playlist creation mode
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import asyncio


@dataclass
class PlaylistSession:
    """Active playlist creation session"""
    user_id: int
    name: str
    track_ids: List[int] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_track(self, track_id: int):
        self.track_ids.append(track_id)
    
    @property
    def track_count(self) -> int:
        return len(self.track_ids)
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        return datetime.utcnow() - self.created_at > timedelta(minutes=timeout_minutes)


class SessionManager:
    """
    Manages user sessions for stateful operations.
    Sessions auto-expire after 30 minutes of inactivity.
    """
    
    def __init__(self):
        self._playlist_sessions: Dict[int, PlaylistSession] = {}
        self._pending_duplicates: Dict[int, dict] = {}  # user_id -> {track_info, playlist_session}
        self._pending_uploads: Dict[int, dict] = {}  # user_id -> pending upload data awaiting confirmation
    
    # Playlist sessions
    def start_playlist_session(self, user_id: int, name: str) -> PlaylistSession:
        """Start a new playlist creation session"""
        session = PlaylistSession(user_id=user_id, name=name)
        self._playlist_sessions[user_id] = session
        return session
    
    def get_playlist_session(self, user_id: int) -> Optional[PlaylistSession]:
        """Get active playlist session for user"""
        session = self._playlist_sessions.get(user_id)
        if session and session.is_expired():
            self.end_playlist_session(user_id)
            return None
        return session
    
    def end_playlist_session(self, user_id: int) -> Optional[PlaylistSession]:
        """End and return playlist session"""
        return self._playlist_sessions.pop(user_id, None)
    
    def has_playlist_session(self, user_id: int) -> bool:
        """Check if user has active playlist session"""
        return self.get_playlist_session(user_id) is not None
    
    # Pending duplicate confirmations
    def set_pending_duplicate(self, user_id: int, track_info: dict):
        """Store pending duplicate track for confirmation"""
        self._pending_duplicates[user_id] = track_info
    
    def get_pending_duplicate(self, user_id: int) -> Optional[dict]:
        """Get pending duplicate info"""
        return self._pending_duplicates.get(user_id)
    
    def clear_pending_duplicate(self, user_id: int):
        """Clear pending duplicate"""
        self._pending_duplicates.pop(user_id, None)
    
    # Pending upload confirmations (for deduplication on upload)
    def set_pending_upload(self, user_id: int, upload_data: dict):
        """Store pending upload awaiting duplicate confirmation"""
        self._pending_uploads[user_id] = upload_data
    
    def get_pending_upload(self, user_id: int) -> Optional[dict]:
        """Get pending upload data"""
        return self._pending_uploads.get(user_id)
    
    def clear_pending_upload(self, user_id: int):
        """Clear pending upload"""
        self._pending_uploads.pop(user_id, None)
    
    # Cleanup
    def cleanup_expired(self):
        """Remove expired sessions"""
        expired = [
            uid for uid, session in self._playlist_sessions.items()
            if session.is_expired()
        ]
        for uid in expired:
            del self._playlist_sessions[uid]


# Global session manager
session_manager = SessionManager()

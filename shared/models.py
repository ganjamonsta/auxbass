"""
TG Player - Database Models
Supports shared global library where all users can see and play each other's tracks
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    BigInteger, Integer, String, Text, Boolean, 
    DateTime, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user_id
    username: Mapped[Optional[str]] = mapped_column(String(255))
    first_name: Mapped[Optional[str]] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255))
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    tracks: Mapped[List["Track"]] = relationship(back_populates="uploader", cascade="all, delete-orphan")
    playlists: Mapped[List["Playlist"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    library_entries: Mapped[List["UserLibrary"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    
    @property
    def display_name(self) -> str:
        """Get user's display name"""
        if self.first_name:
            return f"{self.first_name} {self.last_name or ''}".strip()
        return self.username or f"User {self.id}"


class Track(Base):
    """
    Global track - one instance per unique file across all users.
    Any user can play any track, the uploader just gets credit.
    """
    __tablename__ = "tracks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    file_unique_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)  # Now globally unique!
    
    # Metadata
    title: Mapped[Optional[str]] = mapped_column(String(255))
    artist: Mapped[Optional[str]] = mapped_column(String(255))
    album: Mapped[Optional[str]] = mapped_column(String(255))
    genre: Mapped[Optional[str]] = mapped_column(String(100))
    duration: Mapped[Optional[int]] = mapped_column(Integer)  # seconds
    cover_url: Mapped[Optional[str]] = mapped_column(String(500))  # Album cover URL
    
    # Deezer album ID for auto-album creation
    deezer_album_id: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Album release date from Deezer (YYYY-MM-DD format)
    release_date: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Enrichment status: pending, processing, completed, failed
    enrichment_status: Mapped[Optional[str]] = mapped_column(String(20), default="pending")
    
    # Forward source info (from whom the message was forwarded)
    forward_from_id: Mapped[Optional[int]] = mapped_column(BigInteger)  # User/Bot/Channel ID
    forward_from_username: Mapped[Optional[str]] = mapped_column(String(255))
    forward_from_name: Mapped[Optional[str]] = mapped_column(String(255))
    forward_from_type: Mapped[Optional[str]] = mapped_column(String(20))  # user, bot, channel
    
    # Telegram data
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    mime_type: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Global listening statistics (across all users)
    play_count: Mapped[int] = mapped_column(Integer, default=0)
    last_played_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Visibility in global library
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Availability (file deleted from Telegram)
    is_unavailable: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    uploader: Mapped["User"] = relationship(back_populates="tracks")
    playlist_associations: Mapped[List["PlaylistTrack"]] = relationship(back_populates="track", cascade="all, delete-orphan")
    library_entries: Mapped[List["UserLibrary"]] = relationship(back_populates="track", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_tracks_artist", "artist"),
        Index("idx_tracks_title", "title"),
        Index("idx_tracks_genre", "genre"),
        Index("idx_tracks_public", "is_public"),
        Index("idx_tracks_play_count", "play_count"),
    )


class UserLibrary(Base):
    """
    User's personal library - links users to tracks they've added.
    Each user can have their own liked status, play count, etc.
    """
    __tablename__ = "user_library"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    track_id: Mapped[int] = mapped_column(Integer, ForeignKey("tracks.id", ondelete="CASCADE"))
    
    # How did user get this track
    source: Mapped[str] = mapped_column(String(20), default="uploaded")  # uploaded, added, shared
    
    # Personal stats (per-user)
    is_liked: Mapped[bool] = mapped_column(Boolean, default=False)
    liked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    play_count: Mapped[int] = mapped_column(Integer, default=0)
    last_played_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Timestamps
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relations
    user: Mapped["User"] = relationship(back_populates="library_entries")
    track: Mapped["Track"] = relationship(back_populates="library_entries")
    
    __table_args__ = (
        UniqueConstraint("user_id", "track_id", name="uq_user_library_track"),
        Index("idx_user_library_user", "user_id"),
        Index("idx_user_library_liked", "user_id", "is_liked"),
    )


class Playlist(Base):
    __tablename__ = "playlists"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    cover_file_id: Mapped[Optional[str]] = mapped_column(String(255))
    cover_url: Mapped[Optional[str]] = mapped_column(String(500))  # Album cover from Deezer
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_auto_album: Mapped[bool] = mapped_column(Boolean, default=False)  # Auto-created album
    deezer_album_id: Mapped[Optional[int]] = mapped_column(Integer)  # Deezer album ID
    album_artist: Mapped[Optional[str]] = mapped_column(String(255))  # Artist for album playlists
    release_date: Mapped[Optional[str]] = mapped_column(String(20))  # Album release date (YYYY-MM-DD format)
    
    # Auto-source playlist (auto-created based on forward source)
    is_auto_source: Mapped[bool] = mapped_column(Boolean, default=False)
    source_id: Mapped[Optional[int]] = mapped_column(BigInteger)  # Forward source ID
    source_type: Mapped[Optional[str]] = mapped_column(String(20))  # user, bot, channel
    
    share_code: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    user: Mapped["User"] = relationship(back_populates="playlists")
    track_associations: Mapped[List["PlaylistTrack"]] = relationship(
        back_populates="playlist", 
        cascade="all, delete-orphan",
        order_by="PlaylistTrack.position"
    )
    
    @property
    def tracks(self) -> List["Track"]:
        return [assoc.track for assoc in self.track_associations]


class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    playlist_id: Mapped[int] = mapped_column(Integer, ForeignKey("playlists.id", ondelete="CASCADE"))
    track_id: Mapped[int] = mapped_column(Integer, ForeignKey("tracks.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relations
    playlist: Mapped["Playlist"] = relationship(back_populates="track_associations")
    track: Mapped["Track"] = relationship(back_populates="playlist_associations")
    
    __table_args__ = (
        UniqueConstraint("playlist_id", "track_id", name="uq_playlist_track"),
    )

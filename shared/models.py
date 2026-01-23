"""
TG Player - Database Models
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
    tracks: Mapped[List["Track"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    playlists: Mapped[List["Playlist"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Track(Base):
    __tablename__ = "tracks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    file_unique_id: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Metadata
    title: Mapped[Optional[str]] = mapped_column(String(255))
    artist: Mapped[Optional[str]] = mapped_column(String(255))
    album: Mapped[Optional[str]] = mapped_column(String(255))
    genre: Mapped[Optional[str]] = mapped_column(String(100))
    duration: Mapped[Optional[int]] = mapped_column(Integer)  # seconds
    cover_url: Mapped[Optional[str]] = mapped_column(String(500))  # Album cover URL
    
    # Enrichment status: pending, processing, completed, failed
    enrichment_status: Mapped[Optional[str]] = mapped_column(String(20), default="pending")
    
    # Telegram data
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    mime_type: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Listening statistics
    play_count: Mapped[int] = mapped_column(Integer, default=0)
    last_played_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Favorites
    is_liked: Mapped[bool] = mapped_column(Boolean, default=False)
    liked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    user: Mapped["User"] = relationship(back_populates="tracks")
    playlist_associations: Mapped[List["PlaylistTrack"]] = relationship(back_populates="track", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("user_id", "file_unique_id", name="uq_user_track"),
        Index("idx_tracks_artist", "artist"),
        Index("idx_tracks_title", "title"),
        Index("idx_tracks_genre", "genre"),
    )


class Playlist(Base):
    __tablename__ = "playlists"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    cover_file_id: Mapped[Optional[str]] = mapped_column(String(255))
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
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

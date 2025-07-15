"""Zotero sync tracking model."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Integer, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class ZoteroSync(Base):
    """Track synchronization between Zotero and local papers."""
    
    __tablename__ = "zotero_sync"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Zotero identifiers
    zotero_key: Mapped[str] = mapped_column(String(50), nullable=False)  # Unique item key from Zotero
    zotero_version: Mapped[int] = mapped_column(Integer, nullable=False)  # Version for change detection
    
    # Local paper reference
    paper_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    
    # User who owns this sync
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Sync metadata
    last_synced: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    sync_status: Mapped[str] = mapped_column(String(50), default="synced")  # synced, pending, error
    sync_error: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Relationships
    paper: Mapped["Paper"] = relationship("Paper", back_populates="zotero_sync")
    user: Mapped["User"] = relationship("User", back_populates="zotero_syncs")
    
    # Ensure unique Zotero items per user
    __table_args__ = (
        UniqueConstraint('user_id', 'zotero_key', name='_user_zotero_key_uc'),
    )


class ZoteroConfig(Base):
    """Store Zotero API configuration per user."""
    
    __tablename__ = "zotero_config"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User reference
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Zotero API credentials (encrypted in production)
    api_key: Mapped[str] = mapped_column(String(100), nullable=False)
    zotero_user_id: Mapped[str] = mapped_column(String(50), nullable=False)  # Numeric Zotero user ID
    
    # Sync settings
    auto_sync_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sync_interval_minutes: Mapped[int] = mapped_column(Integer, default=30)
    last_sync: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_sync_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="zotero_config")
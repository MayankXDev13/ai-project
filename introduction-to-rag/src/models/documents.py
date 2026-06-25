from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4
from sqlmodel import Field, SQLModel
from enum import Enum


def _uuid() -> str:
    return str(uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Document(SQLModel, table=True):
    __tablename__ = "documents"
    id: str = Field(default_factory=_uuid, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True, nullable=False)
    title: Optional[str] = Field(default=None)
    original_filename: str = Field(nullable=False)
    storage_path: str = Field(nullable=False)
    mime_type: str = Field(nullable=False)
    qdrant_collection_id: Optional[str] = Field(default=None)
    qdrant_document_id: Optional[str] = Field(default=None)
    status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)
    processing_error: Optional[str] = None
    deleted_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

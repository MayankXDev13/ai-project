from typing import List, Optional
from datetime import datetime, timezone
from uuid import uuid4
from sqlmodel import SQLModel, Field, Relationship

def _uuid() -> str:
    return str(uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: str = Field(default_factory=_uuid, primary_key=True)
    email: str = Field(index=True, nullable=False, unique=True)
    hash_password: str = Field(nullable=False)
    deleted_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

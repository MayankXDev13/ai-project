from src.models import User
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum


def _uuid() -> str:
    return str(uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)

class VerificationTokenType(str, Enum):
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"

class VerificationToken(SQLModel, table=True):
    __tablename__ = "verification_tokens"

    id: str = Field(default_factory=_uuid, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    token_hash: str
    type: VerificationTokenType
    expires_at: datetime
    used_at: Optional[datetime] = None
    device_name: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    user: Optional["User"] = Relationship(back_populates="verification_tokens")

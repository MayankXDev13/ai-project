from datetime import datetime, timezone
from uuid import uuid4
from sqlmodel import Field, SQLModel
from enum import Enum


def _uuid() -> str:
    return str(uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: str = Field(default_factory=_uuid, primary_key=True)
    chat_session_id: str = Field(foreign_key="chat_sessions.id", index=True, nullable=False)
    role: MessageRole
    content: str
    created_at: datetime = Field(default_factory=_now)

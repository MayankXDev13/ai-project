from openai.types.beta.chatkit import ChatSession
from openpyxl.packaging.relationship import Relationship
from langchain_core.documents import Document
from ast import List
from sqlalchemy.orm import Mapped
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4
from sqlmodel import Field, SQLModel

def _uuid() -> str:
    return str(uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: str = Field(default_factory=_uuid, primary_key=True)
    email: str = Field(index=True, nullable=False, unique=True)
    hash_password: str = Field(nullable=False)
    documents: Mapped[List["Document"]] = Relationship(back_populates="owner")  
    chat_sessions: Mapped[List["ChatSession"]] = Relationship(back_populates="owner")
    deleted_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from src.models.messages import MessageRole

class CreateSessionRequest(BaseModel):
    document_id: str

class CreateSessionResponse(BaseModel):
    id: str
    document_id: str
    title: str

class SessionResponse(BaseModel):
    id: str
    document_id: str
    title: str
    created_at: datetime

class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]

class SendMessageRequest(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: str
    role: MessageRole
    content: str
    created_at: datetime

class MessageListResponse(BaseModel):
    messages: list[MessageResponse]

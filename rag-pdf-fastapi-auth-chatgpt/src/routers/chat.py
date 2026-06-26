from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from src.db.database import get_session
from src.models.chats import ChatSession
from src.models.messages import Message, MessageRole
from src.models.documents import Document, ProcessingStatus
from src.schemas.chat import (
    CreateSessionRequest,
    CreateSessionResponse,
    SessionResponse,
    SessionListResponse,
    SendMessageRequest,
    MessageResponse,
    MessageListResponse,
)
from src.services.rag_service import query as rag_query
from src.utils.dependencies import get_current_user
from src.models.users import User

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/sessions", response_model=CreateSessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    body: CreateSessionRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    doc = session.exec(
        select(Document).where(
            Document.id == body.document_id,
            Document.user_id == user.id,
            Document.deleted_at.is_(None),
        )
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if doc.status != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document is {doc.status.value}, must be completed",
        )

    chat = ChatSession(user_id=user.id, document_id=doc.id)
    session.add(chat)
    session.commit()
    session.refresh(chat)

    return CreateSessionResponse(id=chat.id, document_id=chat.document_id, title=chat.title)

@router.get("/sessions", response_model=SessionListResponse)
def list_sessions(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == user.id, ChatSession.deleted_at.is_(None))
        .order_by(ChatSession.created_at.desc())
    )
    chats = session.exec(stmt).all()
    return SessionListResponse(
        sessions=[
            SessionResponse(id=c.id, document_id=c.document_id, title=c.title, created_at=c.created_at)
            for c in chats
        ]
    )

@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
def send_message(
    session_id: str,
    body: SendMessageRequest,
    user: User = Depends(get_current_user),
    db_session: Session = Depends(get_session),
):
    chat = db_session.exec(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id,
            ChatSession.deleted_at.is_(None),
        )
    ).first()

    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")

    user_msg = Message(chat_session_id=chat.id, role=MessageRole.USER, content=body.content)
    db_session.add(user_msg)
    db_session.commit()

    doc = db_session.get(Document, chat.document_id)
    if not doc or doc.status != ProcessingStatus.COMPLETED or not doc.qdrant_collection_id:
        assistant_msg = Message(
            chat_session_id=chat.id,
            role=MessageRole.ASSISTANT,
            content="Document is still processing or unavailable.",
        )
        db_session.add(assistant_msg)
        db_session.commit()
        db_session.refresh(assistant_msg)
        return MessageResponse(id=assistant_msg.id, role=assistant_msg.role, content=assistant_msg.content, created_at=assistant_msg.created_at)

    try:
        answer = rag_query(doc.qdrant_collection_id, body.content)
    except Exception as e:
        answer = f"Error querying document: {str(e)}"

    assistant_msg = Message(chat_session_id=chat.id, role=MessageRole.ASSISTANT, content=answer)
    db_session.add(assistant_msg)
    db_session.commit()
    db_session.refresh(assistant_msg)

    return MessageResponse(id=assistant_msg.id, role=assistant_msg.role, content=assistant_msg.content, created_at=assistant_msg.created_at)

@router.get("/sessions/{session_id}/messages", response_model=MessageListResponse)
def get_messages(
    session_id: str,
    user: User = Depends(get_current_user),
    db_session: Session = Depends(get_session),
):
    chat = db_session.exec(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id,
            ChatSession.deleted_at.is_(None),
        )
    ).first()

    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")

    stmt = (
        select(Message)
        .where(Message.chat_session_id == chat.id)
        .order_by(Message.created_at)
    )
    messages = db_session.exec(stmt).all()

    return MessageListResponse(
        messages=[
            MessageResponse(id=m.id, role=m.role, content=m.content, created_at=m.created_at)
            for m in messages
        ]
    )

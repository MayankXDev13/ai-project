import os
import uuid as uuid_lib
import aiofiles
from sqlmodel import Session, select
from fastapi import UploadFile
from src.models.documents import Document, ProcessingStatus
from src.config.config import UPLOAD_DIR

async def save_upload_file(user_id: str, file: UploadFile) -> str:
    filename = (file.filename or "").lower()

    if not filename.endswith(".pdf"):
        raise ValueError("Only PDF files are supported")

    user_dir = os.path.join(UPLOAD_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)

    file_uuid = str(uuid_lib.uuid4())
    safe_filename = f"{file_uuid}_{file.filename}"
    file_path = os.path.join(user_dir, safe_filename)

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    return file_path

async def create_document_record(
    session: Session,
    user_id: str,
    filename: str,
    storage_path: str,
    mime_type: str,
) -> Document:
    doc = Document(
        user_id=user_id,
        original_filename=filename,
        storage_path=storage_path,
        mime_type=mime_type,
        status=ProcessingStatus.PENDING,
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc

async def get_user_documents(session: Session, user_id: str) -> list[Document]:
    stmt = (
        select(Document)
        .where(Document.user_id == user_id, Document.deleted_at.is_(None))
        .order_by(Document.created_at.desc())
    )
    return session.exec(stmt).all()

async def get_document(session: Session, document_id: str, user_id: str) -> Document | None:
    stmt = select(Document).where(
        Document.id == document_id,
        Document.user_id == user_id,
        Document.deleted_at.is_(None),
    )
    return session.exec(stmt).first()

async def delete_document(session: Session, document: Document) -> None:
    from datetime import datetime, timezone
    document.deleted_at = datetime.now(timezone.utc)
    session.add(document)
    session.commit()

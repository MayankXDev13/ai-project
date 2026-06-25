from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from sqlmodel import Session
from src.db.database import get_session
from src.schemas.documents import UploadResponse, DocumentResponse, DocumentListResponse
from src.services.document_service import save_upload_file, create_document_record, get_user_documents, get_document, delete_document
from src.services.background import process_pdf_background
from src.utils.dependencies import get_current_user
from src.models.users import User

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        storage_path = await save_upload_file(user.id, file)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    doc = create_document_record(
        session=session,
        user_id=user.id,
        filename=file.filename,
        storage_path=storage_path,
        mime_type=file.content_type or "application/pdf",
    )

    background_tasks.add_task(process_pdf_background, doc.id)

    return UploadResponse(id=doc.id, status=doc.status)

@router.get("", response_model=DocumentListResponse)
def list_documents(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    docs = get_user_documents(session, user.id)
    return DocumentListResponse(
        documents=[
            DocumentResponse(
                id=d.id,
                title=d.title,
                original_filename=d.original_filename,
                mime_type=d.mime_type,
                status=d.status,
                processing_error=d.processing_error,
                created_at=d.created_at,
            )
            for d in docs
        ]
    )

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document_route(
    document_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    doc = get_document(session, document_id, user.id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        original_filename=doc.original_filename,
        mime_type=doc.mime_type,
        status=doc.status,
        processing_error=doc.processing_error,
        created_at=doc.created_at,
    )

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_route(
    document_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    doc = get_document(session, document_id, user.id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    delete_document(session, doc)

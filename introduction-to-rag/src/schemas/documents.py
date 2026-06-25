from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from src.models.documents import ProcessingStatus

class UploadResponse(BaseModel):
    id: str
    status: ProcessingStatus

class DocumentResponse(BaseModel):
    id: str
    title: Optional[str]
    original_filename: str
    mime_type: str
    status: ProcessingStatus
    processing_error: Optional[str]
    created_at: datetime

class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]

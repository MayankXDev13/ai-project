from sqlmodel import Session
from src.db.database import engine
from src.models.documents import Document, ProcessingStatus
from src.services.rag_service import process_pdf, embed_and_store


def process_document_job(document_id: str) -> None:
    """RQ job: process a PDF document end-to-end and store embeddings."""
    with Session(engine) as session:
        doc = session.get(Document, document_id)
        if not doc:
            return

        try:
            doc.status = ProcessingStatus.PROCESSING
            session.add(doc)
            session.commit()

            collection_name = f"doc_{document_id}"
            langchain_docs = process_pdf(doc.storage_path)

            if not langchain_docs:
                raise ValueError("No text could be extracted from the PDF")

            embed_and_store(langchain_docs, collection_name)

            doc.status = ProcessingStatus.COMPLETED
            doc.qdrant_collection_id = collection_name
            session.add(doc)
            session.commit()

        except Exception as e:
            doc.status = ProcessingStatus.FAILED
            doc.processing_error = str(e)
            session.add(doc)
            session.commit()

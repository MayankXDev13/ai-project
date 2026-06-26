import io
from unittest.mock import patch
from datetime import datetime, timezone
from sqlmodel import Session, select

from src.models.documents import Document, ProcessingStatus
from src.models.chats import ChatSession
from src.models.messages import Message
from tests.conftest import test_engine, override_get_session


def _complete_document(client, auth_headers, test_user):
    """Upload a PDF and mark it as completed directly in the DB."""
    with patch("src.routers.documents.queue.enqueue"):
        resp = client.post(
            "/api/documents/upload",
            headers=auth_headers,
            files={"file": ("report.pdf", io.BytesIO(b"%PDF-1.4 data"), "application/pdf")},
        )
    doc_id = resp.json()["id"]

    gen = override_get_session()
    session = next(gen)
    doc = session.get(Document, doc_id)
    doc.status = ProcessingStatus.COMPLETED
    doc.qdrant_collection_id = f"doc_{doc_id}"
    session.add(doc)
    session.commit()
    session.close()

    return doc_id


def test_create_chat_session(client, auth_headers, test_user):
    doc_id = _complete_document(client, auth_headers, test_user)

    response = client.post(
        "/api/chat/sessions",
        headers=auth_headers,
        json={"document_id": doc_id},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["document_id"] == doc_id
    assert "id" in data
    assert data["title"] == "New Chat"


def test_create_session_on_pending_document(client, auth_headers, test_user):
    with patch("src.routers.documents.queue.enqueue"):
        resp = client.post(
            "/api/documents/upload",
            headers=auth_headers,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 data"), "application/pdf")},
        )
    doc_id = resp.json()["id"]

    response = client.post(
        "/api/chat/sessions",
        headers=auth_headers,
        json={"document_id": doc_id},
    )
    assert response.status_code == 400
    assert "completed" in response.json()["detail"].lower()


def test_create_session_document_not_found(client, auth_headers):
    response = client.post(
        "/api/chat/sessions",
        headers=auth_headers,
        json={"document_id": "nonexistent-id"},
    )
    assert response.status_code == 404


def test_list_chat_sessions(client, auth_headers, test_user):
    doc_id = _complete_document(client, auth_headers, test_user)

    client.post(
        "/api/chat/sessions",
        headers=auth_headers,
        json={"document_id": doc_id},
    )

    response = client.get("/api/chat/sessions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["sessions"]) == 1
    assert data["sessions"][0]["document_id"] == doc_id


@patch("src.routers.chat.rag_query", return_value="This is a mock RAG answer.")
def test_send_message(mock_rag, client, auth_headers, test_user):
    doc_id = _complete_document(client, auth_headers, test_user)

    session_resp = client.post(
        "/api/chat/sessions",
        headers=auth_headers,
        json={"document_id": doc_id},
    )
    session_id = session_resp.json()["id"]

    response = client.post(
        f"/api/chat/sessions/{session_id}/messages",
        headers=auth_headers,
        json={"content": "What is this document about?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "assistant"
    assert data["content"] == "This is a mock RAG answer."
    mock_rag.assert_called_once()


def test_get_messages(client, auth_headers, test_user):
    doc_id = _complete_document(client, auth_headers, test_user)

    session_resp = client.post(
        "/api/chat/sessions",
        headers=auth_headers,
        json={"document_id": doc_id},
    )
    session_id = session_resp.json()["id"]

    with patch("src.services.rag_service.query", return_value="Mock answer"):
        client.post(
            f"/api/chat/sessions/{session_id}/messages",
            headers=auth_headers,
            json={"content": "First question"},
        )
        client.post(
            f"/api/chat/sessions/{session_id}/messages",
            headers=auth_headers,
            json={"content": "Second question"},
        )

    response = client.get(
        f"/api/chat/sessions/{session_id}/messages",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["messages"]) == 4
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][1]["role"] == "assistant"
    assert data["messages"][2]["role"] == "user"
    assert data["messages"][3]["role"] == "assistant"


def test_send_message_session_not_found(client, auth_headers):
    response = client.post(
        "/api/chat/sessions/nonexistent/messages",
        headers=auth_headers,
        json={"content": "Hello"},
    )
    assert response.status_code == 404


def test_get_messages_session_not_found(client, auth_headers):
    response = client.get(
        "/api/chat/sessions/nonexistent/messages",
        headers=auth_headers,
    )
    assert response.status_code == 404

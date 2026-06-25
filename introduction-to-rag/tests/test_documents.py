import io
from unittest.mock import patch


def test_upload_pdf(client, auth_headers):
    with patch("src.routers.documents.queue.enqueue") as mock_enqueue:
        response = client.post(
            "/api/documents/upload",
            headers=auth_headers,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 fake content"), "application/pdf")},
        )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "pending"
    mock_enqueue.assert_called_once()


def test_upload_non_pdf_rejected(client, auth_headers):
    response = client.post(
        "/api/documents/upload",
        headers=auth_headers,
        files={"file": ("test.txt", io.BytesIO(b"not a pdf"), "text/plain")},
    )
    assert response.status_code == 400
    assert "pdf" in response.json()["detail"].lower()


def test_upload_without_auth(client):
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )
    assert response.status_code == 401


def test_list_documents(client, auth_headers):
    with patch("src.routers.documents.queue.enqueue"):
        client.post(
            "/api/documents/upload",
            headers=auth_headers,
            files={"file": ("doc1.pdf", io.BytesIO(b"%PDF-1.4 content"), "application/pdf")},
        )
        client.post(
            "/api/documents/upload",
            headers=auth_headers,
            files={"file": ("doc2.pdf", io.BytesIO(b"%PDF-1.4 content"), "application/pdf")},
        )

    response = client.get("/api/documents", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["documents"]) == 2


def test_get_document(client, auth_headers):
    with patch("src.routers.documents.queue.enqueue"):
        upload_resp = client.post(
            "/api/documents/upload",
            headers=auth_headers,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 content"), "application/pdf")},
        )
    doc_id = upload_resp.json()["id"]

    response = client.get(f"/api/documents/{doc_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc_id
    assert data["original_filename"] == "test.pdf"
    assert data["status"] == "pending"


def test_get_document_not_found(client, auth_headers):
    response = client.get("/api/documents/nonexistent-id", headers=auth_headers)
    assert response.status_code == 404


def test_delete_document(client, auth_headers):
    with patch("src.routers.documents.queue.enqueue"):
        upload_resp = client.post(
            "/api/documents/upload",
            headers=auth_headers,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 content"), "application/pdf")},
        )
    doc_id = upload_resp.json()["id"]

    response = client.delete(f"/api/documents/{doc_id}", headers=auth_headers)
    assert response.status_code == 204

    get_resp = client.get(f"/api/documents/{doc_id}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_delete_document_not_found(client, auth_headers):
    response = client.delete("/api/documents/nonexistent-id", headers=auth_headers)
    assert response.status_code == 404


def test_documents_isolated_between_users(client, auth_headers):
    with patch("src.routers.documents.queue.enqueue"):
        client.post(
            "/api/documents/upload",
            headers=auth_headers,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 content"), "application/pdf")},
        )

    other_resp = client.post("/api/auth/register", json={
        "email": "other@example.com",
        "password": "pass123",
    })
    other_user = other_resp.json()

    from src.lib.security import create_access_token
    other_headers = {"Authorization": f"Bearer {create_access_token({'sub': other_user['id']})}"}

    response = client.get("/api/documents", headers=other_headers)
    assert response.status_code == 200
    assert len(response.json()["documents"]) == 0

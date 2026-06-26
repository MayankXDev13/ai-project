import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from unittest.mock import patch

from src.main import app
from src.db.database import get_session
from src.lib.security import create_access_token
from src.models.users import User
from src.models.documents import Document
from src.models.chats import ChatSession
from src.models.messages import Message

_db_file = os.path.join(tempfile.gettempdir(), "rag_test.db")
test_engine = create_engine(
    f"sqlite:///{_db_file}",
    connect_args={"check_same_thread": False},
)


def override_get_session():
    with Session(test_engine) as session:
        yield session


@pytest.fixture(autouse=True)
def db_setup_teardown():
    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture
def client():
    app.dependency_overrides[get_session] = override_get_session
    with patch("src.main.create_tables"):
        with TestClient(app) as c:
            yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(client):
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "testpass123",
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def auth_headers(test_user):
    token = create_access_token({"sub": test_user["id"]})
    return {"Authorization": f"Bearer {token}"}

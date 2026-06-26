def test_register_success(client):
    response = client.post("/api/auth/register", json={
        "email": "new@example.com",
        "password": "secret123",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@example.com"
    assert "id" in data


def test_register_duplicate_email(client, test_user):
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "testpass123",
    })
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"].lower()


def test_login_success(client, test_user):
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, test_user):
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpass",
    })
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    response = client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "testpass123",
    })
    assert response.status_code == 401


def test_me_success(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


def test_me_no_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_invalid_token(client):
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == 401


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

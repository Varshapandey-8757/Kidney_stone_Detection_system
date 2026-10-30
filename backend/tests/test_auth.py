def test_register_login_refresh_and_logout(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "Test Person",
            "email": "Person@Example.com",
            "password": "Strong-Pass-123",
        },
    )
    assert response.status_code == 201
    assert response.json()["user"]["email"] == "person@example.com"
    assert "refresh_token" in client.cookies

    login = client.post(
        "/auth/login",
        json={"email": "PERSON@example.com", "password": "Strong-Pass-123"},
    )
    assert login.status_code == 200
    assert login.json()["access_token"]

    refreshed = client.post("/auth/refresh")
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]

    logout = client.post("/auth/logout")
    assert logout.status_code == 204
    assert client.post("/auth/refresh").status_code == 401


def test_register_rejects_weak_password_and_duplicate_email(client):
    body = {
        "name": "Test Person",
        "email": "person@example.com",
        "password": "weak",
    }
    assert client.post("/auth/register", json=body).status_code == 422

    body["password"] = "Strong-Pass-123"
    assert client.post("/auth/register", json=body).status_code == 201
    assert client.post("/auth/register", json=body).status_code == 409


def test_register_rejects_name_with_only_whitespace(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "  ",
            "email": "person@example.com",
            "password": "Strong-Pass-123",
        },
    )
    assert response.status_code == 422


def test_inactive_user_cannot_login(client, make_user):
    make_user(active=False)
    response = client.post(
        "/auth/login",
        json={"email": "person@example.com", "password": "Strong-Pass-123"},
    )
    assert response.status_code == 401


def test_protected_profile_requires_auth_and_returns_current_user(client, auth_headers):
    assert client.get("/auth/me").status_code == 401
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "person@example.com"

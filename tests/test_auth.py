def test_signup_creates_user_without_leaking_password(client):
    r = client.post("/auth/signup", json={"email": "a@example.com", "password": "secret123"})
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "a@example.com"
    assert "password" not in body and "password_hash" not in body


def test_duplicate_signup_rejected(client):
    client.post("/auth/signup", json={"email": "a@example.com", "password": "secret123"})
    r = client.post("/auth/signup", json={"email": "a@example.com", "password": "other123"})
    assert r.status_code == 409


def test_invalid_email_and_short_password_rejected(client):
    assert client.post("/auth/signup", json={"email": "nope", "password": "secret123"}).status_code == 422
    assert client.post("/auth/signup", json={"email": "b@example.com", "password": "123"}).status_code == 422


def test_login_returns_token(client):
    client.post("/auth/signup", json={"email": "a@example.com", "password": "secret123"})
    r = client.post("/auth/login", data={"username": "a@example.com", "password": "secret123"})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_login_wrong_password_and_unknown_email_look_identical(client):
    client.post("/auth/signup", json={"email": "a@example.com", "password": "secret123"})
    wrong_pw = client.post("/auth/login", data={"username": "a@example.com", "password": "bad"})
    unknown = client.post("/auth/login", data={"username": "ghost@example.com", "password": "bad"})
    assert wrong_pw.status_code == unknown.status_code == 401
    assert wrong_pw.json() == unknown.json()


def test_me_requires_valid_token(client, auth_headers):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401
    r = client.get("/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["email"] == "priya@example.com"

"""
Shared test fixtures.

Each test gets a brand-new, empty in-memory SQLite database, so tests are
isolated from each other and never touch your real data.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # one shared connection = one shared in-memory DB
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def _signup_and_login(client, email: str, password: str = "secret123") -> dict:
    client.post("/auth/signup", json={"email": email, "password": password})
    r = client.post("/auth/login", data={"username": email, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def auth_headers(client):
    return _signup_and_login(client, "priya@example.com")


@pytest.fixture()
def other_headers(client):
    return _signup_and_login(client, "arjun@example.com")

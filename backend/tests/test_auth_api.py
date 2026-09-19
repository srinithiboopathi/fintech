"""
Integration Tests for Authentication API Endpoints (/api/v1/auth/).
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.db.database import Base, get_db

# Test SQLite in-memory database with StaticPool so all sessions share the in-memory state
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


def test_register_api_success(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "analyst@quantlab.io",
            "password": "StrongPassword123!",
            "full_name": "Quant Researcher",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "analyst@quantlab.io"
    assert data["user"]["full_name"] == "Quant Researcher"
    assert data["user"]["is_active"] is True
    assert "hashed_password" not in data["user"]


def test_register_api_duplicate_email(client):
    payload = {
        "email": "duplicate@quantlab.io",
        "password": "Password123!",
        "full_name": "Analyst One",
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_register_api_invalid_email(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "Password123!",
        },
    )
    assert response.status_code == 422


def test_register_api_short_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "valid@quantlab.io",
            "password": "123",  # Less than min_length=6
        },
    )
    assert response.status_code == 422


def test_login_api_success(client):
    # Register user first
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "trader@quantlab.io",
            "password": "TradingPassword2025!",
            "full_name": "Desk Trader",
        },
    )

    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "trader@quantlab.io",
            "password": "TradingPassword2025!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "trader@quantlab.io"


def test_login_api_wrong_password(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "trader@quantlab.io",
            "password": "TradingPassword2025!",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "trader@quantlab.io",
            "password": "IncorrectPassword!",
        },
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_api_unknown_user(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "ghost@quantlab.io",
            "password": "AnyPassword123!",
        },
    )
    assert response.status_code == 401


def test_get_me_with_valid_token(client):
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "me_test@quantlab.io",
            "password": "MePassword123!",
            "full_name": "Me Analyst",
        },
    )
    token = reg_res.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == "me_test@quantlab.io"
    assert user_data["full_name"] == "Me Analyst"


def test_get_me_unauthorized_missing_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_me_unauthorized_invalid_token(client):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.fake.jwt.token"},
    )
    assert response.status_code == 401


def test_logout_endpoint(client):
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert "Successfully logged out" in response.json()["message"]

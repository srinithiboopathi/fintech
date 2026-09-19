"""
Unit Tests for Authentication Security & AuthService.
"""
import pytest
from datetime import timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from backend.app.db.database import Base
from backend.app.models.user import User
from backend.app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from backend.app.schemas.auth import UserRegisterRequest
from backend.app.services.auth_service import AuthService


@pytest.fixture
def test_db():
    """In-memory SQLite database session for unit tests."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_hash_password_and_verify():
    pwd = "QuantSecurePassword2025!"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert hashed.startswith("$2b$")
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False
    assert verify_password("", hashed) is False


def test_create_and_decode_access_token():
    payload = {"sub": "42", "email": "analyst@quantlab.io"}
    token = create_access_token(payload, expires_delta=timedelta(minutes=15))
    assert isinstance(token, str)
    assert len(token) > 20

    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded.get("sub") == "42"
    assert decoded.get("email") == "analyst@quantlab.io"
    assert "exp" in decoded


def test_expired_access_token():
    payload = {"sub": "42", "email": "analyst@quantlab.io"}
    # Token expired 10 minutes ago
    expired_token = create_access_token(payload, expires_delta=timedelta(minutes=-10))
    decoded = decode_access_token(expired_token)
    assert decoded is None


def test_invalid_token_decoding():
    assert decode_access_token("not.a.valid.jwt.token") is None
    assert decode_access_token("") is None


def test_auth_service_register_user(test_db):
    req = UserRegisterRequest(
        email="Researcher1@QuantLab.io",
        password="ValidPassword123!",
        full_name="Lead Quant Analyst",
    )
    user = AuthService.register_user(test_db, req)
    assert user.id is not None
    assert user.email == "researcher1@quantlab.io"  # Lowercase normalized
    assert user.full_name == "Lead Quant Analyst"
    assert user.is_active is True
    assert user.hashed_password != "ValidPassword123!"
    assert verify_password("ValidPassword123!", user.hashed_password) is True


def test_auth_service_duplicate_email(test_db):
    req1 = UserRegisterRequest(
        email="analyst@quantlab.io",
        password="Password123!",
        full_name="Analyst One",
    )
    AuthService.register_user(test_db, req1)

    req2 = UserRegisterRequest(
        email="ANALYST@quantlab.io",
        password="DifferentPassword456!",
        full_name="Analyst Two",
    )
    with pytest.raises(HTTPException) as exc_info:
        AuthService.register_user(test_db, req2)
    assert exc_info.value.status_code == 400
    assert "already exists" in exc_info.value.detail


def test_auth_service_authenticate_user_success(test_db):
    req = UserRegisterRequest(
        email="quant@quantlab.io",
        password="SecretPassword888!",
        full_name="Quant Operator",
    )
    AuthService.register_user(test_db, req)

    # Valid credentials
    user = AuthService.authenticate_user(test_db, "quant@quantlab.io", "SecretPassword888!")
    assert user is not None
    assert user.email == "quant@quantlab.io"

    # Case insensitive email
    user_upper = AuthService.authenticate_user(test_db, "QUANT@QUANTLAB.IO", "SecretPassword888!")
    assert user_upper is not None
    assert user_upper.id == user.id


def test_auth_service_authenticate_wrong_password(test_db):
    req = UserRegisterRequest(
        email="quant@quantlab.io",
        password="SecretPassword888!",
    )
    AuthService.register_user(test_db, req)

    user = AuthService.authenticate_user(test_db, "quant@quantlab.io", "IncorrectPassword!")
    assert user is None


def test_auth_service_authenticate_unknown_user(test_db):
    user = AuthService.authenticate_user(test_db, "nonexistent@quantlab.io", "SomePassword!")
    assert user is None

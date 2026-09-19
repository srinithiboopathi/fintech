"""
Authentication Service for QUANTLAB.
"""
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.app.models.user import User
from backend.app.schemas.auth import UserRegisterRequest
from backend.app.core.security import hash_password, verify_password, create_access_token


class AuthService:
    """
    Manages user registration, credential authentication, and JWT lifecycle.
    """

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        normalized_email = email.strip().lower()
        return db.query(User).filter(User.email == normalized_email).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def register_user(db: Session, request: UserRegisterRequest) -> User:
        normalized_email = request.email.strip().lower()

        # Check if email is already registered
        existing_user = AuthService.get_user_by_email(db, normalized_email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists.",
            )

        # Hash password and create record
        hashed_pwd = hash_password(request.password)
        new_user = User(
            email=normalized_email,
            hashed_password=hashed_pwd,
            full_name=request.full_name.strip() if request.full_name else None,
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        normalized_email = email.strip().lower()
        user = AuthService.get_user_by_email(db, normalized_email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    @staticmethod
    def generate_token_for_user(user: User) -> str:
        payload = {
            "sub": str(user.id),
            "email": user.email,
        }
        return create_access_token(payload)


auth_service = AuthService()

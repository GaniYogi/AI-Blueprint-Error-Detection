from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.database import get_db
from app.db import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEFAULT_USER_EMAIL = "architect@blueprint.ai"
DEFAULT_USER_NAME = "Architect User"
DEFAULT_USER_PASSWORD = "blueprint_default_pass_2026"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_current_user(db: Session = Depends(get_db)) -> models.User:
    """
    No-auth mode: always returns the single default user.
    Creates the user in the DB on first run if it doesn't exist yet.
    """
    user = db.query(models.User).filter(
        models.User.email == DEFAULT_USER_EMAIL
    ).first()

    if user is None:
        user = models.User(
            email=DEFAULT_USER_EMAIL,
            hashed_password=get_password_hash(DEFAULT_USER_PASSWORD),
            full_name=DEFAULT_USER_NAME,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user

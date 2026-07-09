"""Authentication business logic."""

from loguru import logger
from sqlalchemy.orm import Session

from app.backend.auth.security import create_access_token, hash_password, verify_password
from app.backend.core.exceptions import AppException
from app.backend.models.user import User
from app.backend.schemas.token import Token
from app.backend.schemas.user import UserCreate, UserLogin


def register_user(payload: UserCreate, db: Session) -> User:
    """Register a new user after validating uniqueness.

    Raises:
        AppException 409: if the email is already registered.
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        logger.warning(f"Registration attempt with duplicate email: {payload.email}")
        raise AppException("Email already registered.", status_code=409)

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"New user registered: {user.email} (id={user.id})")
    return user


def authenticate_user(payload: UserLogin, db: Session) -> Token:
    """Authenticate a user and return a JWT access token.

    Raises:
        AppException 401: if credentials are invalid or account is inactive.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        logger.warning(f"Failed login attempt for email: {payload.email}")
        raise AppException("Invalid email or password.", status_code=401)

    if not user.is_active:
        logger.warning(f"Login attempt on inactive account: {payload.email}")
        raise AppException("Account is inactive.", status_code=403)

    token = create_access_token(user_id=user.id, email=user.email)
    logger.info(f"User logged in: {user.email} (id={user.id})")
    return Token(access_token=token)

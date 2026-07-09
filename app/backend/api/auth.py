"""Authentication API router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.backend.auth.dependencies import get_current_user
from app.backend.database.session import get_db
from app.backend.models.user import User
from app.backend.schemas.token import Token
from app.backend.schemas.user import UserCreate, UserLogin, UserResponse
from app.backend.services.auth_service import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    """Register a new user account."""
    return register_user(payload, db)


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    """Authenticate and return a JWT access token."""
    return authenticate_user(payload, db)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> User:
    """Return the profile of the currently authenticated user."""
    return current_user


@router.post("/logout", status_code=200)
def logout() -> dict[str, str]:
    """Invalidate session on the client side.

    JWT tokens are stateless; this endpoint signals the client to
    discard its stored token.
    """
    return {"message": "Logged out successfully."}

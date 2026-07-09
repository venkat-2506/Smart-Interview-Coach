"""FastAPI dependency that resolves the current authenticated user."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.backend.auth.security import decode_access_token
from app.backend.database.session import get_db
from app.backend.models.user import User

_bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Resolve and return the authenticated user from the JWT token.

    Raises:
        HTTPException 401: if the token is missing, invalid, or the user
        does not exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token_data = decode_access_token(credentials.credentials)
    except JWTError:
        raise credentials_exception

    user = db.get(User, token_data.user_id)
    if user is None or not user.is_active:
        raise credentials_exception
    return user

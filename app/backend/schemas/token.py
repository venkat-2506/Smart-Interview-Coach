"""Pydantic schemas for JWT token operations."""

from pydantic import BaseModel


class Token(BaseModel):
    """Schema for access token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for data encoded inside a JWT token."""

    user_id: int | None = None
    email: str | None = None

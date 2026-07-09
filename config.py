"""Application configuration."""

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    """Centralized application settings loaded from environment variables."""

    gemini_api_key: str = Field(default="")
    secret_key: str = Field(default="change-me-in-production")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    database_url: str = Field(default="sqlite:///./data/interview_coach.db")

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        return cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            secret_key=os.getenv("SECRET_KEY", "change-me-in-production"),
            algorithm=os.getenv("ALGORITHM", "HS256"),
            access_token_expire_minutes=int(
                os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
            ),
            database_url=os.getenv(
                "DATABASE_URL", "sqlite:///./data/interview_coach.db"
            ),
        )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings.from_env()
"""FastAPI application factory."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from loguru import logger

from app.backend.core.handlers import register_exception_handlers
from app.backend.utils.logger import setup_logger
from config import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown."""
    setup_logger()
    get_settings()
    logger.info("Smart Interview Coach API started")
    yield
    logger.info("Smart Interview Coach API stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Smart Interview Coach API",
        version="1.0.0",
        description="AI-powered interview preparation platform backend.",
        lifespan=lifespan,
    )

    register_exception_handlers(app)

    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint confirming the backend is running."""
        return {"message": "Smart Interview Coach Backend Running"}

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}

    return app

"""FastAPI application factory."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from loguru import logger

from app.backend.core.handlers import register_exception_handlers
from app.backend.utils.logger import setup_logger
from app.backend.database.session import engine, Base
# Import models so SQLAlchemy knows about them before creating tables
from app.backend.models.user import User
from app.backend.models.resume import Resume
from app.backend.api.auth import router as auth_router
from app.backend.api.resume import router as resume_router
from config import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown."""
    setup_logger()
    get_settings()
    
    logger.info("Initializing database...")
    # This automatically creates all tables that inherit from Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")
    
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
    
    # Register routers for Authentication and Resume
    app.include_router(auth_router)
    app.include_router(resume_router)

    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint confirming the backend is running."""
        return {"message": "Smart Interview Coach Backend Running"}

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}

    return app

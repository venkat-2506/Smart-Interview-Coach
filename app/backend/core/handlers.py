"""Global exception handlers."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from app.backend.core.exceptions import AppException


async def app_exception_handler(
    _request: Request, exc: AppException
) -> JSONResponse:
    """Handle known application exceptions."""
    logger.error(exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


async def generic_exception_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI application."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

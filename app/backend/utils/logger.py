"""Centralized logging configuration."""

import sys

from loguru import logger


def setup_logger() -> None:
    """Configure Loguru for console and error logging."""
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )
    logger.add(
        sys.stderr,
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        filter=lambda record: record["level"].name == "ERROR",
    )

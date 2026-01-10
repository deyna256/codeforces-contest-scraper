"""Logging configuration for codeforces-editorial-finder."""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from config import get_settings


def setup_logger(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    verbose: bool = False,
) -> None:
    """
    Configure logger with specified settings.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (None for stdout only)
        verbose: If True, use DEBUG level regardless of other settings
    """
    # Remove default logger
    logger.remove()

    # Get settings
    settings = get_settings()

    # Determine log level
    if verbose:
        log_level = "DEBUG"
    elif level:
        log_level = level.upper()
    else:
        log_level = settings.log_level

    # Add stdout handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # Add file handler if specified
    file_path = log_file or settings.log_file
    if file_path:
        log_path = Path(file_path).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_path,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
            "{name}:{function}:{line} | {message}",
            level=log_level,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
        )
        logger.debug(f"Logging to file: {log_path}")

    logger.debug(f"Logger initialized with level: {log_level}")


def get_logger(name: str):
    """Get a logger instance for the given name."""
    return logger.bind(name=name)


# Default initialization
_initialized = False


def ensure_logger_initialized() -> None:
    """Ensure logger is initialized with default settings."""
    global _initialized
    if not _initialized:
        setup_logger()
        _initialized = True

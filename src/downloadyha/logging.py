"""
Structured logging module for Downloadyha.

Provides logging functionality with platform-specific log file storage
in the application data directory.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .paths import get_log_dir


def get_log_file_path() -> Path:
    """
    Get the path to the log file.

    Returns:
        Path to the log file in the application's log directory.
    """
    log_dir = get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)

    # Use date-based log file name
    date_str = datetime.now().strftime("%Y-%m-%d")
    return log_dir / f"downloadyha-{date_str}.log"


def setup_logging(
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = False
) -> logging.Logger:
    """
    Configure and return the application logger.

    Args:
        level: Logging level (default: logging.INFO).
        log_to_file: Whether to write logs to file (default: True).
        log_to_console: Whether to write logs to console (default: False).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("downloadyha")
    logger.setLevel(level)

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Add file handler
    if log_to_file:
        try:
            log_file = get_log_file_path()
            file_handler = logging.FileHandler(
                log_file,
                mode="a",
                encoding="utf-8"
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # If file logging fails, continue without it
            logger.warning(f"Could not set up file logging: {e}")

    # Add console handler only if a valid stream exists
    if log_to_console and sys.stdout is not None and hasattr(sys.stdout, "write"):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Optional sub-logger name. If provided, returns a child logger.

    Returns:
        Logger instance for the given name, or the main downloadyha logger.
    """
    if name:
        return logging.getLogger(f"downloadyha.{name}")
    return logging.getLogger("downloadyha")


def log_download_start(url: str, download_type: str, quality: str) -> None:
    """
    Log the start of a download.

    Args:
        url: The YouTube URL being downloaded.
        download_type: "audio" or "video".
        quality: The selected quality.
    """
    logger = get_logger("download")
    logger.info(
        f"Download started: type={download_type}, quality={quality}, url={url}"
    )


def log_download_success(output_path: str) -> None:
    """
    Log a successful download.

    Args:
        output_path: Path to the downloaded file.
    """
    logger = get_logger("download")
    logger.info(f"Download completed successfully: {output_path}")


def log_download_error(error: Exception, url: str) -> None:
    """
    Log a download error.

    Args:
        error: The exception that occurred.
        url: The YouTube URL that failed.
    """
    logger = get_logger("download")
    logger.error(f"Download failed for {url}: {error}")


def log_dependency_check(dependency: str, found: bool, path: str = None) -> None:
    """
    Log dependency verification results.

    Args:
        dependency: Name of the dependency (e.g., "ffmpeg", "deno").
        found: Whether the dependency was found.
        path: Path to the dependency if found.
    """
    logger = get_logger("dependencies")
    if found:
        logger.debug(f"Dependency '{dependency}' found at: {path}")
    else:
        logger.warning(f"Dependency '{dependency}' not found")


def log_error(message: str, exception: Optional[Exception] = None) -> None:
    """
    Log a general error.

    Args:
        message: Error message.
        exception: Optional exception that caused the error.
    """
    logger = get_logger("error")
    if exception:
        logger.error(f"{message}: {exception}", exc_info=True)
    else:
        logger.error(message)

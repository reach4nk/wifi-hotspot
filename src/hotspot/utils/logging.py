"""Logging utilities for the hotspot package."""

from __future__ import annotations

import logging
import sys
from typing import Optional


_LOGGER: Optional[logging.Logger] = None


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for terminal output."""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    level: int = logging.INFO,
    use_color: bool = True,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """Configure logging for the application.

    Args:
        level: Logging level (default: INFO).
        use_color: Whether to use colored output for terminal.
        log_file: Optional file path to write logs to.

    Returns:
        Configured logger instance.
    """
    global _LOGGER

    _LOGGER = logging.getLogger("hotspot")
    _LOGGER.setLevel(level)
    _LOGGER.handlers.clear()

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)

    if use_color and sys.stderr.isatty():
        console_format = ColoredFormatter(
            "%(levelname)s: %(message)s",
            style="%",
        )
    else:
        console_format = logging.Formatter(
            "%(levelname)s: %(message)s",
            style="%",
        )
    console_handler.setFormatter(console_format)
    _LOGGER.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            style="%",
        )
        file_handler.setFormatter(file_format)
        _LOGGER.addHandler(file_handler)

    return _LOGGER


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Optional logger name (sub-logger). If None, returns root logger.

    Returns:
        Logger instance.
    """
    if _LOGGER is None:
        setup_logging()

    if name:
        return _LOGGER.getChild(name)
    return _LOGGER

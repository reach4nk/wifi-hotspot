"""Unit tests for logging utilities."""

from __future__ import annotations

import logging
from unittest.mock import patch, MagicMock

import pytest

from hotspot.utils.logging import (
    ColoredFormatter,
    setup_logging,
    get_logger,
    _LOGGER,
)


class TestColoredFormatter:
    """Tests for ColoredFormatter class."""

    def test_format_info(self):
        """Test formatting INFO level."""
        formatter = ColoredFormatter("%(levelname)s: %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        assert "INFO" in result
        assert "Test message" in result

    def test_format_error(self):
        """Test formatting ERROR level."""
        formatter = ColoredFormatter("%(levelname)s: %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Error message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        assert "ERROR" in result

    def test_format_warning(self):
        """Test formatting WARNING level."""
        formatter = ColoredFormatter("%(levelname)s: %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="Warning message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        assert "WARNING" in result


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_default(self):
        """Test setup with defaults."""
        with patch("logging.getLogger") as mock_get:
            with patch("logging.Handler"):
                mock_logger = MagicMock()
                mock_get.return_value = mock_logger
                result = setup_logging()
                assert result == mock_logger
                mock_logger.setLevel.assert_called_with(logging.INFO)

    def test_setup_logging_debug_level(self):
        """Test setup with DEBUG level."""
        with patch("logging.getLogger") as mock_get:
            with patch("logging.Handler"):
                mock_logger = MagicMock()
                mock_get.return_value = mock_logger
                setup_logging(level=logging.DEBUG)
                mock_logger.setLevel.assert_called_with(logging.DEBUG)

    def test_setup_logging_with_file(self, tmp_path):
        """Test setup with log file."""
        log_file = tmp_path / "test.log"
        with patch("logging.getLogger") as mock_get:
            mock_logger = MagicMock()
            mock_get.return_value = mock_logger
            result = setup_logging(log_file=str(log_file))
            mock_logger.addHandler.assert_called()

    def test_setup_logging_console_handler(self):
        """Test setup adds console handler."""
        with patch("logging.getLogger") as mock_get:
            with patch("logging.StreamHandler") as mock_handler_cls:
                mock_logger = MagicMock()
                mock_handler = MagicMock()
                mock_handler_cls.return_value = mock_handler
                mock_get.return_value = mock_logger
                setup_logging(use_color=False)
                mock_logger.addHandler.assert_called_with(mock_handler)


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_no_name(self):
        """Test get_logger without name."""
        with patch("hotspot.utils.logging._LOGGER", MagicMock()):
            with patch("hotspot.utils.logging.setup_logging"):
                result = get_logger()
                assert result is not None

    def test_get_logger_with_name(self):
        """Test get_logger with name."""
        mock_logger = MagicMock()
        mock_child = MagicMock()
        mock_logger.getChild.return_value = mock_child

        with patch.dict("hotspot.utils.logging.__dict__", {"_LOGGER": mock_logger}):
            with patch("hotspot.utils.logging.setup_logging"):
                result = get_logger("test")
                mock_logger.getChild.assert_called_with("test")

    def test_get_logger_initializes_if_none(self):
        """Test get_logger calls setup if _LOGGER is None."""
        with patch.dict("hotspot.utils.logging.__dict__", {"_LOGGER": None}):
            with patch("hotspot.utils.logging.setup_logging") as mock_setup:
                mock_logger = MagicMock()
                mock_setup.return_value = mock_logger
                result = get_logger()
                mock_setup.assert_called_once()

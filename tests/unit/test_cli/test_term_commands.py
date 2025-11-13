"""Unit tests for term commands file logging functionality."""

import logging
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from xp.cli.commands.term.term_commands import setup_file_logging


class TestFileLogging:
    """Test file logging setup for term commands."""

    def test_file_handler_configuration_with_valid_path(self, tmp_path: Path) -> None:
        """Test that file handler is correctly configured with a valid path.

        Args:
            tmp_path: Pytest temporary directory fixture.
        """
        log_file = tmp_path / "test.log"
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
        date_format = "%H:%M:%S"
        log_level = logging.DEBUG

        # Create a mock config that returns our test log path
        mock_config = MagicMock()
        mock_config.log_path = str(log_file)

        with patch(
            "xp.cli.commands.term.term_commands.ConbusClientConfig.from_yaml",
            return_value=mock_config,
        ):
            # Setup file logging
            setup_file_logging(log_level, log_format, date_format, "test_config.yml")

            # Verify the log file was created
            assert log_file.exists()

            # Get the root logger and check handlers
            root_logger = logging.getLogger()
            file_handlers = [
                h for h in root_logger.handlers if hasattr(h, "baseFilename")
            ]

            # Verify at least one file handler was added
            assert len(file_handlers) > 0

            # Verify the handler points to our log file
            assert any(Path(h.baseFilename) == log_file for h in file_handlers)

            # Write a test log message
            test_logger = logging.getLogger("test_module")
            test_logger.setLevel(logging.DEBUG)
            test_logger.debug("Test message")

            # Flush all handlers to ensure logs are written
            for handler in file_handlers:
                handler.flush()

            # Verify the message was written to the file
            with open(log_file) as f:
                content = f.read()
                assert "Test message" in content

            # Clean up handlers
            for handler in file_handlers:
                handler.close()
                root_logger.removeHandler(handler)

    def test_file_handler_with_config_fallback(self, tmp_path: Path) -> None:
        """Test that file handler falls back to default path when not in config.

        Args:
            tmp_path: Pytest temporary directory fixture.
        """
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
        date_format = "%H:%M:%S"
        log_level = logging.INFO

        # Create a mock config with no log_path
        mock_config = MagicMock()
        mock_config.log_path = None

        with (
            patch(
                "xp.cli.commands.term.term_commands.ConbusClientConfig.from_yaml",
                return_value=mock_config,
            ),
            patch("pathlib.Path.home", return_value=tmp_path),
        ):
            # Setup file logging
            setup_file_logging(log_level, log_format, date_format, "test_config.yml")

            # Verify the default log file was created
            default_log = tmp_path / ".xp" / "logs" / "term.log"
            assert default_log.exists()

            # Clean up handlers
            root_logger = logging.getLogger()
            file_handlers = [
                h for h in root_logger.handlers if hasattr(h, "baseFilename")
            ]
            for handler in file_handlers:
                handler.close()
                root_logger.removeHandler(handler)

    def test_file_handler_creates_directory(self, tmp_path: Path) -> None:
        """Test that file handler auto-creates log directory if missing.

        Args:
            tmp_path: Pytest temporary directory fixture.
        """
        log_dir = tmp_path / "new" / "log" / "directory"
        log_file = log_dir / "test.log"
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
        date_format = "%H:%M:%S"
        log_level = logging.DEBUG

        # Verify directory doesn't exist yet
        assert not log_dir.exists()

        # Create a mock config
        mock_config = MagicMock()
        mock_config.log_path = str(log_file)

        with patch(
            "xp.cli.commands.term.term_commands.ConbusClientConfig.from_yaml",
            return_value=mock_config,
        ):
            # Setup file logging
            setup_file_logging(log_level, log_format, date_format, "test_config.yml")

            # Verify directory was created
            assert log_dir.exists()
            assert log_file.exists()

            # Clean up handlers
            root_logger = logging.getLogger()
            file_handlers = [
                h for h in root_logger.handlers if hasattr(h, "baseFilename")
            ]
            for handler in file_handlers:
                handler.close()
                root_logger.removeHandler(handler)

    def test_file_handler_failure_handling(self, tmp_path: Path) -> None:
        """Test that application continues when file logging fails.

        Args:
            tmp_path: Pytest temporary directory fixture.
        """
        # Create a read-only directory
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only

        log_file = readonly_dir / "test.log"
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
        date_format = "%H:%M:%S"
        log_level = logging.DEBUG

        # Create a mock config
        mock_config = MagicMock()
        mock_config.log_path = str(log_file)

        with (
            patch(
                "xp.cli.commands.term.term_commands.ConbusClientConfig.from_yaml",
                return_value=mock_config,
            ),
            patch("logging.Logger.warning") as mock_warning,
        ):
            # This should not raise an exception
            setup_file_logging(log_level, log_format, date_format, "test_config.yml")

            # Verify warning was logged
            assert mock_warning.call_count >= 1
            warning_messages = [str(call[0][0]) for call in mock_warning.call_args_list]
            assert any("Failed to setup file logging" in msg for msg in warning_messages)

        # Clean up
        readonly_dir.chmod(0o755)

    def test_rotating_file_handler_configuration(self, tmp_path: Path) -> None:
        """Test that RotatingFileHandler is configured with correct parameters.

        Args:
            tmp_path: Pytest temporary directory fixture.
        """
        log_file = tmp_path / "test.log"
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
        date_format = "%H:%M:%S"
        log_level = logging.DEBUG

        # Create a mock config
        mock_config = MagicMock()
        mock_config.log_path = str(log_file)

        with patch(
            "xp.cli.commands.term.term_commands.ConbusClientConfig.from_yaml",
            return_value=mock_config,
        ):
            # Setup file logging
            setup_file_logging(log_level, log_format, date_format, "test_config.yml")

            # Get the root logger and find our file handler
            root_logger = logging.getLogger()
            from logging.handlers import RotatingFileHandler

            file_handlers = [
                h
                for h in root_logger.handlers
                if isinstance(h, RotatingFileHandler)
            ]

            # Verify we have a rotating file handler
            assert len(file_handlers) > 0

            handler = file_handlers[0]
            # Verify configuration
            assert handler.maxBytes == 1024 * 1024  # 1MB
            assert handler.backupCount == 365  # 365 backups

            # Clean up handlers
            for handler in file_handlers:
                handler.close()
                root_logger.removeHandler(handler)

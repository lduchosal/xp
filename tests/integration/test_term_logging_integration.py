"""Integration tests for term command file logging."""

import logging
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from xp.cli.commands.term.term_commands import setup_file_logging


class TestTermLoggingIntegration:
    """Integration tests for term command file logging."""

    def test_log_file_creation_and_writing(self, tmp_path: Path) -> None:
        """Test that log file is created and logs are written correctly.

        Args:
            tmp_path: Pytest temporary directory fixture.
        """
        log_file = tmp_path / "logs" / "term.log"
        log_format = "%(asctime)s - [%(threadName)s-%(thread)d] - %(levelname)s - %(name)s - %(message)s"
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

            # Verify log directory and file were created
            assert log_file.parent.exists()
            assert log_file.exists()

            # Write various log levels
            test_logger = logging.getLogger("xp.test.integration")
            test_logger.setLevel(logging.DEBUG)
            test_logger.debug("Debug message")
            test_logger.info("Info message")
            test_logger.warning("Warning message")
            test_logger.error("Error message")

            # Flush handlers to ensure logs are written
            root_logger = logging.getLogger()
            for handler in root_logger.handlers:
                if hasattr(handler, "flush"):
                    handler.flush()

            # Verify all messages were written to file
            with open(log_file) as f:
                content = f.read()
                assert "Debug message" in content
                assert "Info message" in content
                assert "Warning message" in content
                assert "Error message" in content
                assert "xp.test.integration" in content

            # Clean up handlers
            root_logger = logging.getLogger()
            file_handlers = [
                h for h in root_logger.handlers if hasattr(h, "baseFilename")
            ]
            for handler in file_handlers:
                handler.close()
                root_logger.removeHandler(handler)

    def test_log_rotation(self, tmp_path: Path) -> None:
        """Test that log file rotation works correctly.

        Args:
            tmp_path: Pytest temporary directory fixture.
        """
        log_file = tmp_path / "logs" / "term.log"
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
        date_format = "%H:%M:%S"
        log_level = logging.DEBUG

        # Use small maxBytes for testing rotation
        mock_config = MagicMock()
        mock_config.log_path = str(log_file)

        with (
            patch(
                "xp.cli.commands.term.term_commands.ConbusClientConfig.from_yaml",
                return_value=mock_config,
            ),
            patch(
                "xp.cli.commands.term.term_commands.RotatingFileHandler"
            ) as mock_handler_class,
        ):
            # Create directory first
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # Create a real handler for testing
            from logging.handlers import RotatingFileHandler

            real_handler = RotatingFileHandler(
                log_file, maxBytes=100, backupCount=3  # Small size for testing
            )
            mock_handler_class.return_value = real_handler

            # Setup file logging
            setup_file_logging(log_level, log_format, date_format, "test_config.yml")

            # Verify handler was created with correct parameters
            mock_handler_class.assert_called_once()
            call_args = mock_handler_class.call_args
            assert call_args[0][0] == log_file
            assert call_args[1]["maxBytes"] == 1024 * 1024
            assert call_args[1]["backupCount"] == 365

            # Write enough data to trigger rotation
            test_logger = logging.getLogger("xp.test.rotation")
            test_logger.setLevel(logging.DEBUG)
            for i in range(50):
                test_logger.info(f"This is a test message number {i} for rotation")

            # Flush handler
            real_handler.flush()

            # Check if rotation occurred (backup files created)
            log_files = list(log_file.parent.glob("term.log*"))
            # Should have at least the main log file
            assert len(log_files) >= 1

            # Clean up
            real_handler.close()
            root_logger = logging.getLogger()
            root_logger.removeHandler(real_handler)

    def test_log_level_filtering(self, tmp_path: Path) -> None:
        """Test that log level filtering works correctly.

        Args:
            tmp_path: Pytest temporary directory fixture.
        """
        log_file = tmp_path / "logs" / "term.log"
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
        date_format = "%H:%M:%S"
        log_level = logging.WARNING  # Only WARNING and above

        # Create a mock config
        mock_config = MagicMock()
        mock_config.log_path = str(log_file)

        with patch(
            "xp.cli.commands.term.term_commands.ConbusClientConfig.from_yaml",
            return_value=mock_config,
        ):
            # Setup file logging with WARNING level
            setup_file_logging(log_level, log_format, date_format, "test_config.yml")

            # Write various log levels
            test_logger = logging.getLogger("xp.test.filtering")
            test_logger.debug("Debug message - should not appear")
            test_logger.info("Info message - should not appear")
            test_logger.warning("Warning message - should appear")
            test_logger.error("Error message - should appear")

            # Verify only WARNING and above were written
            with open(log_file) as f:
                content = f.read()
                assert "Debug message" not in content
                assert "Info message" not in content
                assert "Warning message" in content
                assert "Error message" in content

            # Clean up handlers
            root_logger = logging.getLogger()
            file_handlers = [
                h for h in root_logger.handlers if hasattr(h, "baseFilename")
            ]
            for handler in file_handlers:
                handler.close()
                root_logger.removeHandler(handler)

    def test_concurrent_logging(self, tmp_path: Path) -> None:
        """Test that concurrent logging from multiple modules works.

        Args:
            tmp_path: Pytest temporary directory fixture.
        """
        log_file = tmp_path / "logs" / "term.log"
        log_format = "%(asctime)s - %(name)s - %(message)s"
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

            # Create multiple loggers
            logger1 = logging.getLogger("xp.service.conbus")
            logger2 = logging.getLogger("xp.service.telegram")
            logger3 = logging.getLogger("xp.service.homekit")

            # Set log level for each logger
            logger1.setLevel(logging.DEBUG)
            logger2.setLevel(logging.DEBUG)
            logger3.setLevel(logging.DEBUG)

            # Write from multiple loggers
            logger1.info("Message from conbus")
            logger2.info("Message from telegram")
            logger3.info("Message from homekit")

            # Flush handlers to ensure logs are written
            root_logger = logging.getLogger()
            for handler in root_logger.handlers:
                if hasattr(handler, "flush"):
                    handler.flush()

            # Verify all messages were written
            with open(log_file) as f:
                content = f.read()
                assert "Message from conbus" in content
                assert "xp.service.conbus" in content
                assert "Message from telegram" in content
                assert "xp.service.telegram" in content
                assert "Message from homekit" in content
                assert "xp.service.homekit" in content

            # Clean up handlers
            root_logger = logging.getLogger()
            file_handlers = [
                h for h in root_logger.handlers if hasattr(h, "baseFilename")
            ]
            for handler in file_handlers:
                handler.close()
                root_logger.removeHandler(handler)

"""Logging service for XP application."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from xp.models.conbus.conbus_logger_config import ConbusLoggerConfig


class LoggerService:
    """Service for managing logging configuration and setup."""

    def __init__(self, logger_config: ConbusLoggerConfig):
        """Initialize LoggerService with configuration.

        Args:
            logger_config: Logger configuration object.
        """
        self.logging_config = logger_config.log
        self.logger = logging.getLogger(__name__)

    def setup(self) -> None:
        """Setup file logging only with configured levels."""
        # Setup file logging for term app (console logging disabled)
        root_logger = logging.getLogger()

        # Remove any existing console handlers
        root_logger.handlers = [
            h
            for h in root_logger.handlers
            if not isinstance(h, logging.StreamHandler)
            or isinstance(h, RotatingFileHandler)
        ]

        # Set root logger level
        numeric_level = getattr(logging, self.logging_config.default_level.upper())
        root_logger.setLevel(numeric_level)

        self.setup_file_logging(
            self.logging_config.log_format, self.logging_config.date_format
        )

        for module in self.logging_config.levels.keys():
            logging.getLogger(module).setLevel(self.logging_config.levels[module])

    def setup_console_logging(self, log_format: str, date_format: str) -> None:
        """Setup console logging with specified format.

        Args:
            log_format: Log message format string.
            date_format: Date format string for log timestamps.
        """
        # Force format on root logger and all handlers
        formatter = logging.Formatter(log_format, datefmt=date_format)
        root_logger = logging.getLogger()

        # Set log level from CLI argument
        numeric_level = getattr(logging, self.logging_config.default_level.upper())
        root_logger.setLevel(numeric_level)

        # Update all existing handlers or create new one
        if root_logger.handlers:
            for handler in root_logger.handlers:
                handler.setFormatter(formatter)
        else:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            root_logger.addHandler(handler)

    def setup_file_logging(self, log_format: str, date_format: str) -> None:
        """Setup file logging with rotation for term application.

        Args:
            log_format: Log message format string.
            date_format: Date format string for log timestamps.
        """
        log_path = Path(self.logging_config.path)
        log_level = self.logging_config.default_level

        try:
            # Create log directory if it doesn't exist
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # Create rotating file handler
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=self.logging_config.max_bytes,
                backupCount=self.logging_config.backup_count,
            )

            # Configure formatter to match console format
            formatter = logging.Formatter(log_format, datefmt=date_format)
            file_handler.setFormatter(formatter)
            file_handler.setLevel(log_level)

            # Attach to root logger
            root_logger = logging.getLogger()
            root_logger.addHandler(file_handler)

        except (OSError, PermissionError) as e:
            self.logger.warning(f"Failed to setup file logging at {log_path}: {e}")
            self.logger.warning("Continuing without file logging")

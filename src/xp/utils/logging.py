import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from xp.models.conbus.conbus_logger_config import ConbusLoggerConfig


class LoggerService:

    def __init__(self, logger_config: ConbusLoggerConfig):
        self.logging_config = logger_config.log
        self.logger = logging.getLogger(__name__)

    def setup(self) -> None:
        # Configure logging with thread information
        log_format = "%(asctime)s - [%(threadName)s-%(thread)d] - %(levelname)s - %(name)s - %(message)s"
        date_format = "%H:%M:%S"

        # Setup file logging for term app
        self.setup_console_logging(log_format, date_format)
        self.setup_file_logging(log_format, date_format)

        for module in self.logging_config.levels.keys():
            logging.getLogger(module).setLevel(self.logging_config.levels[module])

    def setup_console_logging(self,
        log_format: str, date_format: str) -> None:

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

    def setup_file_logging(self,
        log_format: str, date_format: str
    ) -> None:
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

            # Create rotating file handler (1MB max, 365 backups)
            file_handler = RotatingFileHandler(
                log_path, maxBytes=1024 * 1024, backupCount=365
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

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from xp.models.conbus.conbus_client_config import LoggingConfig, ConbusClientConfig


class LoggerService:

    def __init__(self, client_config: ConbusClientConfig):
        self.logging_config = client_config.log

    def setup(self) -> None:
        # Configure logging with thread information
        log_format = "%(asctime)s - [%(threadName)s-%(thread)d] - %(levelname)s - %(name)s - %(message)s"
        date_format = "%H:%M:%S"

        # Setup file logging for term app
        self.setup_console_logging(log_format, date_format)
        self.setup_file_logging(log_format, date_format)

    def setup_console_logging(self,
        log_format: str, date_format: str) -> None:

        # Force format on root logger and all handlers
        formatter = logging.Formatter(log_format, datefmt=date_format)
        root_logger = logging.getLogger()

        # Set log level from CLI argument
        numeric_level = getattr(logging, self.logging_config.level.upper())
        root_logger.setLevel(numeric_level)

        # Update all existing handlers or create new one
        if root_logger.handlers:
            for handler in root_logger.handlers:
                handler.setFormatter(formatter)
        else:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            root_logger.addHandler(handler)

        # Suppress pyhap.hap_protocol logs

        # bubus
        # logging.getLogger("bubus").setLevel(logging.WARNING)

        # xp
        # logging.getLogger("xp").setLevel(logging.DEBUG)
        # logging.getLogger("xp.services.homekit").setLevel(logging.DEBUG)

        # pyhap
        # logging.getLogger("pyhap").setLevel(logging.WARNING)
        # logging.getLogger("pyhap.hap_handler").setLevel(logging.WARNING)
        # logging.getLogger("pyhap.hap_protocol").setLevel(logging.WARNING)
        # logging.getLogger('pyhap.accessory_driver').setLevel(logging.WARNING)


    def setup_file_logging(self,
        log_format: str, date_format: str
    ) -> None:
        """Setup file logging with rotation for term application.

        Args:
            log_format: Log message format string.
            date_format: Date format string for log timestamps.
        """
        logger = logging.getLogger(__name__)
        log_path = Path(self.logging_config.path)
        log_level = self.logging_config.level

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

            logger.info(f"File logging enabled: {log_path}")

        except (OSError, PermissionError) as e:
            logger.warning(f"Failed to setup file logging at {log_path}: {e}")
            logger.warning("Continuing without file logging")

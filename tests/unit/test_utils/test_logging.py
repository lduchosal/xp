"""Unit tests for LoggerService."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from xp.models.conbus.conbus_logger_config import ConbusLoggerConfig, LoggingConfig
from xp.utils.logging import LoggerService


class TestLoggerService:
    """Test cases for LoggerService."""

    @pytest.fixture
    def mock_logger_config(self):
        """Create a mock logger configuration."""
        config = ConbusLoggerConfig(
            log=LoggingConfig(
                path="/tmp/test.log",
                default_level="INFO",
                levels={
                    "xp": logging.DEBUG,
                    "bubus": logging.WARNING,
                },
            )
        )
        return config

    @pytest.fixture
    def logger_service(self, mock_logger_config):
        """Create a LoggerService instance with mock config."""
        return LoggerService(logger_config=mock_logger_config)

    def test_init(self, mock_logger_config):
        """Test LoggerService initialization."""
        service = LoggerService(logger_config=mock_logger_config)

        assert service.logging_config == mock_logger_config.log
        assert service.logger is not None
        assert isinstance(service.logger, logging.Logger)

    @patch("xp.utils.logging.logging.getLogger")
    def test_setup_calls_all_methods(self, mock_get_logger, logger_service):
        """Test that setup() calls setup_file_logging."""
        with patch.object(logger_service, "setup_file_logging") as mock_file:
            logger_service.setup()

            # Verify file logging setup was called
            mock_file.assert_called_once()

    @patch("xp.utils.logging.logging.getLogger")
    def test_setup_console_logging_creates_handler(self, mock_get_logger):
        """Test console logging setup creates handler when none exist."""
        # Setup
        mock_root = MagicMock()
        mock_root.handlers = []
        mock_get_logger.return_value = mock_root

        config = ConbusLoggerConfig(
            log=LoggingConfig(path="/tmp/test.log", default_level="DEBUG", levels={})
        )
        service = LoggerService(logger_config=config)

        # Execute
        service.setup_console_logging(log_format="%(message)s", date_format="%H:%M:%S")

        # Verify
        assert mock_root.addHandler.called
        assert mock_root.setLevel.called
        mock_root.setLevel.assert_called_with(logging.DEBUG)

    @patch("xp.utils.logging.logging.getLogger")
    def test_setup_console_logging_updates_existing_handlers(self, mock_get_logger):
        """Test console logging updates existing handlers."""
        # Setup
        mock_handler1 = MagicMock()
        mock_handler2 = MagicMock()
        mock_root = MagicMock()
        mock_root.handlers = [mock_handler1, mock_handler2]
        mock_get_logger.return_value = mock_root

        config = ConbusLoggerConfig(
            log=LoggingConfig(path="/tmp/test.log", default_level="WARNING", levels={})
        )
        service = LoggerService(logger_config=config)

        # Execute
        service.setup_console_logging(log_format="%(message)s", date_format="%H:%M:%S")

        # Verify both handlers got formatter updated
        assert mock_handler1.setFormatter.called
        assert mock_handler2.setFormatter.called
        assert mock_root.setLevel.called
        mock_root.setLevel.assert_called_with(logging.WARNING)

    @patch("xp.utils.logging.logging.getLogger")
    @patch("xp.utils.logging.RotatingFileHandler")
    @patch("xp.utils.logging.Path")
    def test_setup_file_logging_success(
        self, mock_path, mock_handler_class, mock_get_logger
    ):
        """Test file logging setup with successful file creation."""
        # Setup
        mock_handler = MagicMock()
        mock_handler_class.return_value = mock_handler
        mock_root = MagicMock()
        mock_get_logger.return_value = mock_root

        mock_path_instance = MagicMock()
        mock_path_instance.parent.mkdir = MagicMock()
        mock_path.return_value = mock_path_instance

        config = ConbusLoggerConfig(
            log=LoggingConfig(path="/tmp/test.log", default_level="INFO", levels={})
        )
        service = LoggerService(logger_config=config)

        # Execute
        service.setup_file_logging(log_format="%(message)s", date_format="%H:%M:%S")

        # Verify
        mock_path_instance.parent.mkdir.assert_called_once_with(
            parents=True, exist_ok=True
        )
        mock_handler_class.assert_called_once_with(
            mock_path_instance, maxBytes=1024 * 1024, backupCount=365
        )
        assert mock_handler.setFormatter.called
        assert mock_handler.setLevel.called
        mock_root.addHandler.assert_called_once_with(mock_handler)

    @patch("xp.utils.logging.logging.getLogger")
    @patch("xp.utils.logging.RotatingFileHandler")
    @patch("xp.utils.logging.Path")
    def test_setup_file_logging_handles_permission_error(
        self, mock_path, mock_handler_class, mock_get_logger
    ):
        """Test file logging handles permission errors gracefully."""
        # Setup
        mock_handler_class.side_effect = PermissionError("No permission")
        mock_logger = MagicMock()
        service_logger = MagicMock()
        mock_get_logger.side_effect = lambda name=None: (
            mock_logger if name is None else service_logger
        )

        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance

        config = ConbusLoggerConfig(
            log=LoggingConfig(path="/tmp/test.log", default_level="INFO", levels={})
        )
        service = LoggerService(logger_config=config)
        service.logger = service_logger

        # Execute - should not raise exception
        service.setup_file_logging(log_format="%(message)s", date_format="%H:%M:%S")

        # Verify warning was logged
        assert service_logger.warning.called
        # Should have been called twice - once for the error, once for continuing
        assert service_logger.warning.call_count == 2

    @patch("xp.utils.logging.logging.getLogger")
    @patch("xp.utils.logging.RotatingFileHandler")
    @patch("xp.utils.logging.Path")
    def test_setup_file_logging_handles_os_error(
        self, mock_path, mock_handler_class, mock_get_logger
    ):
        """Test file logging handles OS errors gracefully."""
        # Setup
        mock_path_instance = MagicMock()
        mock_path_instance.parent.mkdir.side_effect = OSError("Disk full")
        mock_path.return_value = mock_path_instance

        mock_logger = MagicMock()
        service_logger = MagicMock()
        mock_get_logger.side_effect = lambda name=None: (
            mock_logger if name is None else service_logger
        )

        config = ConbusLoggerConfig(
            log=LoggingConfig(path="/tmp/test.log", default_level="INFO", levels={})
        )
        service = LoggerService(logger_config=config)
        service.logger = service_logger

        # Execute - should not raise exception
        service.setup_file_logging(log_format="%(message)s", date_format="%H:%M:%S")

        # Verify warning was logged
        assert service_logger.warning.called

    @patch("xp.utils.logging.logging.getLogger")
    def test_setup_module_levels(self, mock_get_logger):
        """Test that setup() configures module-specific log levels."""
        # Setup
        mock_xp_logger = MagicMock()
        mock_bubus_logger = MagicMock()
        mock_root_logger = MagicMock()
        mock_root_logger.handlers = [MagicMock()]

        def get_logger_side_effect(name=None):
            """Return appropriate mock logger based on name.

            Args:
                name: Logger name to retrieve.

            Returns:
                Mock logger instance for the specified name.
            """
            if name is None or name == "":
                return mock_root_logger
            if name == "xp":
                return mock_xp_logger
            if name == "bubus":
                return mock_bubus_logger
            return MagicMock()

        mock_get_logger.side_effect = get_logger_side_effect

        config = ConbusLoggerConfig(
            log=LoggingConfig(
                path="/tmp/test.log",
                default_level="INFO",
                levels={
                    "xp": logging.DEBUG,
                    "bubus": logging.WARNING,
                },
            )
        )
        service = LoggerService(logger_config=config)

        with patch("xp.utils.logging.RotatingFileHandler"):
            with patch("xp.utils.logging.Path"):
                # Execute
                service.setup()

        # Verify module levels were set
        mock_xp_logger.setLevel.assert_called_with(logging.DEBUG)
        mock_bubus_logger.setLevel.assert_called_with(logging.WARNING)

    @patch("xp.utils.logging.logging.getLogger")
    def test_setup_with_empty_levels_dict(self, mock_get_logger):
        """Test setup with empty levels dictionary."""
        # Setup
        mock_root_logger = MagicMock()
        mock_root_logger.handlers = [MagicMock()]
        mock_get_logger.return_value = mock_root_logger

        config = ConbusLoggerConfig(
            log=LoggingConfig(path="/tmp/test.log", default_level="INFO", levels={})
        )
        service = LoggerService(logger_config=config)

        with patch("xp.utils.logging.RotatingFileHandler"):
            with patch("xp.utils.logging.Path"):
                # Execute - should not raise exception
                service.setup()

        # Should complete without errors
        assert True

    def test_file_handler_rotation_params(self):
        """Test that file handler uses correct rotation parameters."""
        with patch("xp.utils.logging.RotatingFileHandler") as mock_handler_class:
            with patch("xp.utils.logging.Path"):
                with patch("xp.utils.logging.logging.getLogger"):
                    config = ConbusLoggerConfig(
                        log=LoggingConfig(
                            path="/tmp/test.log", default_level="INFO", levels={}
                        )
                    )
                    service = LoggerService(logger_config=config)
                    service.setup_file_logging(
                        log_format="%(message)s", date_format="%H:%M:%S"
                    )

                    # Verify rotation parameters from config
                    call_args = mock_handler_class.call_args
                    assert call_args[1]["maxBytes"] == 1024 * 1024  # 1MB default
                    assert call_args[1]["backupCount"] == 365  # Default

    def test_file_handler_custom_rotation_params(self):
        """Test that file handler uses custom rotation parameters from config."""
        with patch("xp.utils.logging.RotatingFileHandler") as mock_handler_class:
            with patch("xp.utils.logging.Path"):
                with patch("xp.utils.logging.logging.getLogger"):
                    config = ConbusLoggerConfig(
                        log=LoggingConfig(
                            path="/tmp/test.log",
                            default_level="INFO",
                            levels={},
                            max_bytes=5 * 1024 * 1024,  # 5MB
                            backup_count=30,
                        )
                    )
                    service = LoggerService(logger_config=config)
                    service.setup_file_logging(
                        log_format="%(message)s", date_format="%H:%M:%S"
                    )

                    # Verify custom rotation parameters
                    call_args = mock_handler_class.call_args
                    assert call_args[1]["maxBytes"] == 5 * 1024 * 1024
                    assert call_args[1]["backupCount"] == 30

    def test_log_format_includes_thread_info(self, logger_service):
        """Test that setup uses log format with thread information."""
        with patch.object(logger_service, "setup_file_logging") as mock_file:
            logger_service.setup()

            # Check that format includes thread info for file logging
            format_arg = mock_file.call_args[0][0]
            assert "%(threadName)s" in format_arg
            assert "%(thread)d" in format_arg

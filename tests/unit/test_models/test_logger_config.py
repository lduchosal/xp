"""Unit tests for logger configuration models."""

import logging
from typing import Dict, Union

import pytest
from pydantic import ValidationError

from xp.models.conbus.conbus_logger_config import ConbusLoggerConfig, LoggingConfig


class TestLoggingConfig:
    """Test cases for LoggingConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = LoggingConfig()

        assert config.path == "log"
        assert config.default_level == "DEBUG"
        assert isinstance(config.levels, dict)
        assert config.max_bytes == 1024 * 1024  # 1MB
        assert config.backup_count == 365
        assert "%(asctime)s" in config.log_format
        assert config.date_format == "%H:%M:%S"

    def test_levels_with_string_names(self):
        """Test that string level names are converted to integers."""
        levels: Dict[str, Union[str, int]] = {
            "xp": "DEBUG",
            "bubus": "WARNING",
            "pyhap": "ERROR",
        }
        config = LoggingConfig(
            path="/tmp/test.log",
            default_level="INFO",
            levels=levels,  # type: ignore[arg-type]
        )

        assert config.levels["xp"] == logging.DEBUG
        assert config.levels["bubus"] == logging.WARNING
        assert config.levels["pyhap"] == logging.ERROR

    def test_levels_with_numeric_values(self):
        """Test that numeric level values are preserved."""
        config = LoggingConfig(
            path="/tmp/test.log",
            default_level="INFO",
            levels={
                "xp": 10,
                "bubus": 30,
                "pyhap": 40,
            },
        )

        assert config.levels["xp"] == 10
        assert config.levels["bubus"] == 30
        assert config.levels["pyhap"] == 40

    def test_levels_mixed_string_and_numeric(self):
        """Test that mixed string and numeric values work."""
        levels: Dict[str, Union[str, int]] = {
            "xp": "DEBUG",
            "bubus": 30,
            "pyhap": "ERROR",
        }
        config = LoggingConfig(
            path="/tmp/test.log",
            default_level="INFO",
            levels=levels,  # type: ignore[arg-type]
        )

        assert config.levels["xp"] == logging.DEBUG
        assert config.levels["bubus"] == 30
        assert config.levels["pyhap"] == logging.ERROR

    def test_levels_case_insensitive(self):
        """Test that level names are case-insensitive."""
        levels: Dict[str, Union[str, int]] = {
            "module1": "debug",
            "module2": "Debug",
            "module3": "DEBUG",
            "module4": "WaRnInG",
        }
        config = LoggingConfig(levels=levels)  # type: ignore[arg-type]

        assert config.levels["module1"] == logging.DEBUG
        assert config.levels["module2"] == logging.DEBUG
        assert config.levels["module3"] == logging.DEBUG
        assert config.levels["module4"] == logging.WARNING

    def test_invalid_level_name_raises_error(self):
        """Test that invalid level names raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            levels: Dict[str, Union[str, int]] = {
                "xp": "INVALID_LEVEL",
            }
            LoggingConfig(levels=levels)  # type: ignore[arg-type]

        error_msg = str(exc_info.value)
        assert "Invalid log level 'INVALID_LEVEL'" in error_msg
        assert "Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL" in error_msg

    def test_all_standard_log_levels(self):
        """Test all standard Python log levels."""
        levels: Dict[str, Union[str, int]] = {
            "debug_mod": "DEBUG",
            "info_mod": "INFO",
            "warning_mod": "WARNING",
            "error_mod": "ERROR",
            "critical_mod": "CRITICAL",
        }
        config = LoggingConfig(levels=levels)  # type: ignore[arg-type]

        assert config.levels["debug_mod"] == logging.DEBUG
        assert config.levels["info_mod"] == logging.INFO
        assert config.levels["warning_mod"] == logging.WARNING
        assert config.levels["error_mod"] == logging.ERROR
        assert config.levels["critical_mod"] == logging.CRITICAL

    def test_custom_rotation_parameters(self):
        """Test custom rotation parameters."""
        config = LoggingConfig(max_bytes=5 * 1024 * 1024, backup_count=30)  # 5MB

        assert config.max_bytes == 5 * 1024 * 1024
        assert config.backup_count == 30

    def test_custom_format_strings(self):
        """Test custom log and date format strings."""
        custom_log_format = "%(levelname)s - %(message)s"
        custom_date_format = "%Y-%m-%d %H:%M:%S"

        config = LoggingConfig(
            log_format=custom_log_format, date_format=custom_date_format
        )

        assert config.log_format == custom_log_format
        assert config.date_format == custom_date_format


class TestConbusLoggerConfig:
    """Test cases for ConbusLoggerConfig model."""

    def test_default_config(self):
        """Test default configuration."""
        config = ConbusLoggerConfig()

        assert config.log is not None
        assert isinstance(config.log, LoggingConfig)

    def test_custom_logging_config(self):
        """Test with custom logging configuration."""
        levels: Dict[str, Union[str, int]] = {
            "xp": "DEBUG",
            "bubus": "WARNING",
        }
        config = ConbusLoggerConfig(
            log=LoggingConfig(
                path="/custom/path.log",
                default_level="ERROR",
                levels=levels,  # type: ignore[arg-type]
            )
        )

        assert config.log.path == "/custom/path.log"
        assert config.log.default_level == "ERROR"
        assert config.log.levels["xp"] == logging.DEBUG
        assert config.log.levels["bubus"] == logging.WARNING

    def test_from_dict(self):
        """Test creating config from dictionary (simulating YAML load)."""
        data = {
            "log": {
                "path": "test.log",
                "default_level": "INFO",
                "levels": {
                    "xp": "DEBUG",
                    "pyhap": "WARNING",
                },
            }
        }

        config = ConbusLoggerConfig(**data)  # type: ignore[arg-type]

        assert config.log.path == "test.log"
        assert config.log.default_level == "INFO"
        assert config.log.levels["xp"] == logging.DEBUG
        assert config.log.levels["pyhap"] == logging.WARNING

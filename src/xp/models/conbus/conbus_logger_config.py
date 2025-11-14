"""Logger configuration models for XP application."""

import logging
from pathlib import Path
from typing import Dict, Union

import yaml
from pydantic import BaseModel, Field, field_validator


class LoggingConfig(BaseModel):
    """Logging configuration.

    Attributes:
        path: log folder.
        default_level: DEBUG, WARNING, INFO, ERROR, CRITICAL.
        levels: Per-module log level overrides.
        max_bytes: Maximum size in bytes before rotating (default: 1MB).
        backup_count: Number of backup files to keep (default: 365).
        log_format: Log message format string.
        date_format: Date format string for timestamps.
    """

    path: str = "log"
    default_level: str = "DEBUG"
    levels: Dict[str, int] = {
        "xp": logging.DEBUG,
        "xp.services.homekit": logging.WARNING,
        "xp.services.server": logging.WARNING,
    }
    max_bytes: int = 1024 * 1024  # 1MB
    backup_count: int = 365
    log_format: str = (
        "%(asctime)s - [%(threadName)s-%(thread)d] - %(levelname)s - %(name)s - %(message)s"
    )
    date_format: str = "%H:%M:%S"

    @field_validator("levels", mode="before")
    @classmethod
    def convert_level_names(cls, v: Dict[str, Union[str, int]]) -> Dict[str, int]:
        """Convert string level names to numeric values.

        Args:
            v: Dictionary with string or int log levels.

        Returns:
            Dictionary with numeric log levels.

        Raises:
            ValueError: If an invalid log level name is provided.
        """
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        result = {}
        for module, level in v.items():
            if isinstance(level, str):
                level_upper = level.upper()
                if level_upper not in level_map:
                    raise ValueError(
                        f"Invalid log level '{level}' for module '{module}'. "
                        f"Must be one of: {', '.join(level_map.keys())}"
                    )
                result[module] = level_map[level_upper]
            else:
                result[module] = level
        return result


class ConbusLoggerConfig(BaseModel):
    """Logging configuration.

    Attributes:
        log: LoggingConfig instance for logging settings.
    """

    log: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def from_yaml(cls, file_path: str) -> "ConbusLoggerConfig":
        """Load configuration from YAML file.

        Args:
            file_path: Path to the YAML configuration file.

        Returns:
            ConbusClientConfig instance loaded from file or default config.
        """
        logger = logging.getLogger(__name__)
        try:
            with Path(file_path).open("r") as file:
                data = yaml.safe_load(file)
                return cls(**data)

        except FileNotFoundError:
            logger.error(f"File {file_path} does not exist, loading default")
            return cls()

        except yaml.YAMLError:
            logger.error(f"File {file_path} is not valid")
            # Return default config if YAML parsing fails
            return cls()

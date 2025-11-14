import logging
from pathlib import Path
from typing import Dict

import yaml
from pydantic import BaseModel, Field


class LoggingConfig(BaseModel):
    """Logging configuration.

    Attributes:
        path: log folder.
        level: DEBUG, WARNING, INFO, ERROR, CRITICAL.
    """

    path: str = "log"
    default_level: str = "DEBUG"
    levels: Dict[str, int] = {
        "xp": logging.DEBUG,
        "xp.services.homekit": logging.WARNING,
        "xp.services.server": logging.WARNING,
    }


class ConbusLoggerConfig(BaseModel):
    """Logging configuration."""
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


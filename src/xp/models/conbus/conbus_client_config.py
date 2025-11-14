"""Conbus client configuration models."""

import logging
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class ClientConfig(BaseModel):
    """Client connection configuration.

    Attributes:
        ip: IP address of the Conbus server.
        port: Port number for the connection.
        timeout: Connection timeout in seconds.
    """

    ip: str = "192.168.1.100"
    port: int = 10001
    timeout: float = 0.1


class ConbusClientConfig(BaseModel):
    """Configuration for Conbus client connection.

    Attributes:
        conbus: Client configuration settings.
    """

    conbus: ClientConfig = Field(default_factory=ClientConfig)

    @classmethod
    def from_yaml(cls, file_path: str) -> "ConbusClientConfig":
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

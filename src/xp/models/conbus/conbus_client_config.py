from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class ClientConfig:

    ip: str = "192.168.1.100"
    port: int = 10001
    timeout: float = 0.1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "ip": self.ip,
            "port": self.port,
            "timeout": self.timeout,
        }


@dataclass
class ConbusClientConfig:
    """Configuration for Conbus client connection"""

    conbus: ClientConfig = field(default_factory=ClientConfig)

    @classmethod
    def from_yaml(cls, file_path: str) -> "ConbusClientConfig":
        try:
            with Path(file_path).open("r") as file:
                data = yaml.safe_load(file)

            # Convert nested dict to ClientConfig if needed
            if "conbus" in data and isinstance(data["conbus"], dict):
                data["conbus"] = ClientConfig(**data["conbus"])

            return cls(**data)
        except (yaml.YAMLError, FileNotFoundError, KeyError, TypeError):
            # Return default config if YAML parsing fails
            return cls()

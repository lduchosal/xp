"""Protocol keys configuration model."""

from pathlib import Path
from typing import Dict

import yaml
from pydantic import BaseModel, Field


class ProtocolKeyConfig(BaseModel):
    """Configuration for a single protocol key.

    Attributes:
        name: Human-readable command name.
        telegrams: List of raw telegram strings to send (without angle brackets).
    """

    name: str = Field(..., description="Human-readable command name")
    telegrams: list[str] = Field(..., description="List of raw telegram strings")


class ProtocolKeysConfig(BaseModel):
    """Protocol keys configuration.

    Attributes:
        protocol: Dictionary mapping key to protocol configuration.
    """

    protocol: Dict[str, ProtocolKeyConfig] = Field(
        default_factory=dict, description="Protocol key mappings"
    )

    @classmethod
    def from_yaml(cls, config_path: Path) -> "ProtocolKeysConfig":
        """Load protocol keys from YAML file.

        Args:
            config_path: Path to YAML configuration file.

        Returns:
            ProtocolKeysConfig instance.
        """
        with config_path.open("r") as f:
            data = yaml.safe_load(f)
        return cls(**data)

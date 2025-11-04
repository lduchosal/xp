"""HomeKit configuration models."""

import logging
from ipaddress import IPv4Address, IPv6Address
from pathlib import Path
from typing import List, Optional, Union

import yaml
from pydantic import BaseModel, Field, IPvAnyAddress


class NetworkConfig(BaseModel):
    """Network configuration settings.

    Attributes:
        ip: IP address for the network connection.
        port: Port number for the network connection.
    """

    ip: Union[IPvAnyAddress, IPv4Address, IPv6Address, str] = "127.0.0.1"
    port: int = 51826


class RoomConfig(BaseModel):
    """Room configuration settings.

    Attributes:
        name: Name of the room.
        accessories: List of accessory identifiers in the room.
    """

    name: str
    accessories: List[str]


class BridgeConfig(BaseModel):
    """HomeKit bridge settings.

    Attributes:
        name: Name of the HomeKit bridge.
        rooms: List of room configurations.
    """

    name: str = "Conson Bridge"
    rooms: List[RoomConfig] = []


class HomekitAccessoryConfig(BaseModel):
    """HomeKit accessory configuration.

    Attributes:
        name: Name of the accessory.
        id: Unique identifier for the accessory.
        serial_number: Serial number of the accessory.
        output_number: Output number for the accessory.
        description: Description of the accessory.
        service: Service type for the accessory.
        on_action: on code for the accessory.
        off_action: off code for the accessory.
        hap_accessory: Optional HAP accessory identifier.
    """

    name: str
    id: str
    serial_number: str
    output_number: int
    description: str
    service: str
    on_action: str
    off_action: str
    hap_accessory: Optional[int] = None


class HomekitConfig(BaseModel):
    """HomeKit bridge configuration.

    Attributes:
        homekit: Network configuration for HomeKit.
        conson: Network configuration for Conson.
        bridge: Bridge configuration settings.
        accessories: List of accessory configurations.
    """

    homekit: NetworkConfig = Field(default_factory=NetworkConfig)
    conson: NetworkConfig = Field(default_factory=NetworkConfig)
    bridge: BridgeConfig = Field(default_factory=BridgeConfig)
    accessories: List[HomekitAccessoryConfig] = []

    @classmethod
    def from_yaml(cls, file_path: str) -> "HomekitConfig":
        """Load configuration from YAML file.

        Args:
            file_path: Path to the YAML configuration file.

        Returns:
            HomekitConfig instance loaded from file or default config.
        """
        if not Path(file_path).exists():
            logger = logging.getLogger(__name__)
            logger.error(f"File {file_path} does not exist, loading default")
            return cls()

        with Path(file_path).open("r") as file:
            data = yaml.safe_load(file)
        return cls(**data)

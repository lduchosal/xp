import logging
from ipaddress import IPv4Address, IPv6Address
from pathlib import Path
from typing import List, Optional, Union

import yaml
from pydantic import BaseModel, Field, IPvAnyAddress


class NetworkConfig(BaseModel):
    ip: Union[IPvAnyAddress, IPv4Address, IPv6Address, str] = "127.0.0.1"
    port: int = 51826


class RoomConfig(BaseModel):
    name: str
    accessories: List[str]


class BridgeConfig(BaseModel):
    name: str = "Conson Bridge"
    rooms: List[RoomConfig] = []


class HomekitAccessoryConfig(BaseModel):
    name: str
    id: str
    serial_number: str
    output_number: int
    description: str
    service: str
    hap_accessory: Optional[int] = None


class HomekitConfig(BaseModel):
    homekit: NetworkConfig = Field(default_factory=NetworkConfig)
    conson: NetworkConfig = Field(default_factory=NetworkConfig)
    bridge: BridgeConfig = Field(default_factory=BridgeConfig)
    accessories: List[HomekitAccessoryConfig] = []

    @classmethod
    def from_yaml(cls, file_path: str) -> "HomekitConfig":
        if not Path(file_path).exists():
            logger = logging.getLogger(__name__)
            logger.error(f"File {file_path} does not exist, loading default")
            return cls()

        with Path(file_path).open("r") as file:
            data = yaml.safe_load(file)
        return cls(**data)

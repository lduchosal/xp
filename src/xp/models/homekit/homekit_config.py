from ipaddress import IPv6Address, IPv4Address
from pathlib import Path
from typing import List, Union

import yaml
from pydantic import BaseModel, IPvAnyAddress


class NetworkConfig(BaseModel):
    ip: Union[IPvAnyAddress, IPv4Address, IPv6Address, str]  # Validates IP addresses
    port: int


class RoomConfig(BaseModel):
    name: str
    accessories: List[str]


class BridgeConfig(BaseModel):
    name: str
    rooms: List[RoomConfig]


class HomekitAccessoryConfig(BaseModel):
    name: str
    id: str
    serial_number: str
    output_number: int
    description: str
    service: str


class HomekitConfig(BaseModel):
    homekit: NetworkConfig
    conson: NetworkConfig
    bridge: BridgeConfig
    accessories: List[HomekitAccessoryConfig]

    @classmethod
    def from_yaml(cls, file_path: str) -> "HomekitConfig":
        with Path(file_path).open("r") as file:
            data = yaml.safe_load(file)
        return cls(**data)

from typing import List

import yaml
from pydantic import BaseModel, IPvAnyAddress

class NetworkConfig(BaseModel):
    ip: IPvAnyAddress  # Validates IP addresses
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
    module: int
    output: int
    description: str
    service: str

class HomekitConfig(BaseModel):
    homekit: NetworkConfig
    conson: NetworkConfig
    bridge: BridgeConfig
    accessories: List[HomekitAccessoryConfig]

    @classmethod
    def from_yaml(cls, file_path: str):
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
        return cls(**data)

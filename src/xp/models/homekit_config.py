from typing import List, Optional

import yaml
from pydantic import BaseModel, IPvAnyAddress


class NetworkConfig(BaseModel):
    ip: IPvAnyAddress  # Validates IP addresses
    port: int
    name: Optional[str]

class Room(BaseModel):
    name: str
    accessories: List[str]

class HomekitAccessoryConfig(BaseModel):
    name: str
    id: str
    module: str
    output: int
    description: str
    location: str
    service: str

class HomekitConfig(BaseModel):
    homekit: NetworkConfig
    conson: NetworkConfig
    rooms: List[Room]
    accessories: List[HomekitAccessoryConfig]

    @classmethod
    def from_yaml(cls, file_path: str):
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
        return cls(**data)

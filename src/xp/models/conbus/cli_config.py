from ipaddress import IPv4Address, IPv6Address
from pathlib import Path
from typing import List, Union

import yaml
from pydantic import BaseModel, IPvAnyAddress
class ConbusConfig(BaseModel):
    ip: str = "127.0.0.1"
    port: int = 10001
    timeout: float = 0.1

class CliConfig(BaseModel):
    conbus: ConbusConfig

    @classmethod
    def from_yaml(cls, file_path: str) -> "CliConfig":
        with Path(file_path).open("r") as file:
            data = yaml.safe_load(file)
        return cls(**data)

from pathlib import Path

import yaml
from pydantic import BaseModel


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

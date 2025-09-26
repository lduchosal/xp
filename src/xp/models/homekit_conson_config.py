from pathlib import Path

from pydantic import BaseModel, IPvAnyAddress
from typing import List, Optional


class ConsonModuleConfig(BaseModel):
    name: str
    serial_number: str
    module_type: str
    module_type_code: int
    link_number: int
    enabled: bool = True
    module_number: Optional[int] = None
    conbus_ip: Optional[IPvAnyAddress] = None
    conbus_port: Optional[int] = None
    sw_version: Optional[str] = None
    hw_version: Optional[str] = None


class ConsonModuleListConfig(BaseModel):
    root: List[ConsonModuleConfig]

    @classmethod
    def from_yaml(cls, file_path: str) -> "ConsonModuleListConfig":
        import yaml

        with Path(file_path).open("r") as file:
            data = yaml.safe_load(file)
        return cls(root=data)

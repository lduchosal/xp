from pydantic import BaseModel, IPvAnyAddress
from typing import List, Optional


class ConsonModule(BaseModel):
    name: str
    serial_number: Optional[str] = None
    module_type: str
    module_type_code: Optional[int] = None
    link_number: Optional[int] = None
    module_number: Optional[str] = None
    conbus_ip: Optional[IPvAnyAddress] = None
    conbus_port: Optional[int] = None
    sw_version: Optional[str] = None
    hw_version: Optional[str] = None


class HomekitModuleConfig(BaseModel):
    modules: List[ConsonModule]

    @classmethod
    def from_yaml(cls, file_path: str):
        import yaml
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
        return cls(**data)


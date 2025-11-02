"""HomeKit configuration models."""

import logging
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, IPvAnyAddress


class ConsonModuleConfig(BaseModel):
    """Configuration for a Conson module.

    Attributes:
        name: Name of the module.
        serial_number: Serial number of the module.
        module_type: Type of the module.
        module_type_code: Numeric code for the module type.
        link_number: Link number for the module.
        enabled: Whether the module is enabled.
        module_number: Optional module number.
        conbus_ip: Optional Conbus IP address.
        conbus_port: Optional Conbus port number.
        sw_version: Optional software version.
        hw_version: Optional hardware version.
        action_table: Optional action table configuration.
        auto_report_status: Optional auto report status.
    """

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
    action_table: Optional[List[str]] = None
    auto_report_status: Optional[str] = None


class ConsonModuleListConfig(BaseModel):
    """Configuration list for Conson modules.

    Attributes:
        root: List of Conson module configurations.
    """

    root: List[ConsonModuleConfig] = []

    @classmethod
    def from_yaml(cls, file_path: str) -> "ConsonModuleListConfig":
        """Load configuration from YAML file.

        Args:
            file_path: Path to the YAML configuration file.

        Returns:
            ConsonModuleListConfig instance loaded from file or default config.
        """
        import yaml

        if not Path(file_path).exists():
            logger = logging.getLogger(__name__)
            logger.error(f"File {file_path} does not exist, loading default")
            return cls()

        with Path(file_path).open("r") as file:
            data = yaml.safe_load(file)
        return cls(root=data)

    def find_module(self, serial_number: str) -> Optional[ConsonModuleConfig]:
        """Find a module by serial number.

        Args:
            serial_number: Module serial number to search for.

        Returns:
            ConsonModuleConfig if found, None otherwise.
        """
        for module in self.root:
            if module.serial_number == serial_number:
                return module
        return None

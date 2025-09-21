import logging
from typing import Optional, List

from xp.models.homekit_conson_config import ConsonModule, HomekitModuleConfig


class HomekitModuleService:

    def __init__(self, config_path: str = "conson.yml"):

        # Set up logging
        self.logger = logging.getLogger(__name__)

        self.modules_config = HomekitModuleConfig.from_yaml(config_path)

    def get_module_by_name(self, name: str) -> Optional[ConsonModule]:
        """Get a module by its name"""
        module = next((module for module in self.modules_config.modules if module.name == name), None)
        self.logger.debug(f"Module search by name '{name}': {'found' if module else 'not found'}")
        return module

    def get_module_by_serial(self, serial_number: str) -> Optional[ConsonModule]:
        """Get a module by its serial number"""
        module = next((module for module in self.modules_config.modules if module.serial_number == serial_number), None)
        self.logger.debug(f"Module search by serial '{serial_number}': {'found' if module else 'not found'}")
        return module

    def get_modules_by_type(self, module_type: str) -> List[ConsonModule]:
        """Get all modules of a specific type"""
        modules = [module for module in self.modules_config.modules if module.module_type == module_type]
        self.logger.debug(f"Found {len(modules)} modules of type '{module_type}'")
        return modules

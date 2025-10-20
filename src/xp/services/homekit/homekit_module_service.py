"""HomeKit Module Service.

This module provides service implementation for HomeKit module management.
"""

import logging
from typing import Optional

from xp.models.homekit.homekit_conson_config import (
    ConsonModuleConfig,
    ConsonModuleListConfig,
)


class HomekitModuleService:
    """Service for managing HomeKit module configurations.

    Attributes:
        logger: Logger instance.
        conson_modules_config: Conson module list configuration.
    """

    def __init__(
        self,
        conson_modules_config: ConsonModuleListConfig,
    ):
        """Initialize the HomeKit module service.

        Args:
            conson_modules_config: Conson module list configuration.
        """
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.conson_modules_config = conson_modules_config

    def get_module_by_serial(self, serial_number: str) -> Optional[ConsonModuleConfig]:
        """Get a module by its serial number.

        Args:
            serial_number: Serial number of the module to find.

        Returns:
            Module configuration if found, None otherwise.
        """
        module = next(
            (
                module
                for module in self.conson_modules_config.root
                if module.serial_number == serial_number
            ),
            None,
        )
        self.logger.debug(
            f"Module search by serial '{serial_number}': {'found' if module else 'not found'}"
        )
        return module

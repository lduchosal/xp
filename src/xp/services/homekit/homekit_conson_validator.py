"""Conson Configuration Validator for HomeKit.

This module validates conson.yml configuration files for HomeKit integration.
"""

from typing import List, Set

from xp.models.homekit.homekit_conson_config import (
    ConsonModuleConfig,
    ConsonModuleListConfig,
)


class ConsonConfigValidator:
    """Validates conson.yml configuration file for HomeKit integration."""

    def __init__(self, config: ConsonModuleListConfig):
        """Initialize the Conson config validator.

        Args:
            config: Conson module list configuration to validate.
        """
        self.config = config

    def validate_unique_names(self) -> List[str]:
        """Validate that all module names are unique.

        Returns:
            List of validation error messages.
        """
        names: Set[str] = set()
        errors = []

        for module in self.config.root:
            if module.name in names:
                errors.append(f"Duplicate module name: {module.name}")
            names.add(module.name)

        return errors

    def validate_unique_serial_numbers(self) -> List[str]:
        """Validate that all serial numbers are unique.

        Returns:
            List of validation error messages.
        """
        serials: Set[str] = set()
        errors = []

        for module in self.config.root:
            if module.serial_number in serials:
                errors.append(f"Duplicate serial number: {module.serial_number}")
            serials.add(module.serial_number)

        return errors

    def validate_module_type_codes(self) -> List[str]:
        """Validate module type code ranges.

        Returns:
            List of validation error messages.
        """
        errors = [
            f"Invalid module_type_code {module.module_type_code} for module {module.name}. Must be between 1 and 255."
            for module in self.config.root
            if not (1 <= module.module_type_code <= 255)
        ]

        return errors

    def validate_network_config(self) -> List[str]:
        """Validate IP/port configuration.

        Returns:
            List of validation error messages.
        """
        errors = [
            f"Invalid conbus_port {module.conbus_port} for module {module.name}. Must be between 1 and 65535."
            for module in self.config.root
            if module.conbus_port is not None and not (1 <= module.conbus_port <= 65535)
        ]

        return errors

    def validate_all(self) -> List[str]:
        """Run all validations and return combined errors.

        Returns:
            List of all validation error messages.
        """
        all_errors = []
        all_errors.extend(self.validate_unique_names())
        all_errors.extend(self.validate_unique_serial_numbers())
        all_errors.extend(self.validate_module_type_codes())
        all_errors.extend(self.validate_network_config())
        return all_errors

    def get_module_by_serial(self, serial_number: str) -> ConsonModuleConfig:
        """Get module configuration by serial number.

        Args:
            serial_number: Serial number of the module to find.

        Returns:
            Module configuration for the specified serial number.

        Raises:
            ValueError: If module with serial number is not found.
        """
        for module in self.config.root:
            if module.serial_number == serial_number:
                return module
        raise ValueError(f"Module with serial number {serial_number} not found")

    def get_all_serial_numbers(self) -> Set[str]:
        """Get all serial numbers from the configuration.

        Returns:
            Set of all serial numbers in the configuration.
        """
        return {module.serial_number for module in self.config.root}

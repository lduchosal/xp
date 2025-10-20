"""HomeKit Configuration Validator.

This module validates HomeKit configuration files for correctness and consistency.
"""

from contextlib import suppress
from typing import List, Set

from xp.models.homekit.homekit_config import HomekitConfig
from xp.services.homekit.homekit_conson_validator import ConsonConfigValidator


class HomekitConfigValidator:
    """Validates homekit.yml configuration file for HomeKit integration."""

    def __init__(self, config: HomekitConfig):
        """Initialize the HomeKit config validator.

        Args:
            config: HomeKit configuration to validate.
        """
        self.config = config

    def validate_unique_accessory_names(self) -> List[str]:
        """Validate that all accessory names are unique.

        Returns:
            List of validation error messages.
        """
        names: Set[str] = set()
        errors = []

        for accessory in self.config.accessories:
            if accessory.name in names:
                errors.append(f"Duplicate accessory name: {accessory.name}")
            names.add(accessory.name)

        return errors

    def validate_service_types(self) -> List[str]:
        """Validate that service types are valid.

        Returns:
            List of validation error messages.
        """
        valid_services = {"lightbulb", "outlet", "dimminglight"}
        errors = [
            (
                f"Invalid "
                f"service type '{accessory.service}' "
                f"for accessory '{accessory.name}'. "
                f"Valid types: {', '.join(valid_services)}"
            )
            for accessory in self.config.accessories
            if accessory.service not in valid_services
        ]

        return errors

    def validate_output_numbers(self) -> List[str]:
        """Validate that output numbers are positive integers.

        Returns:
            List of validation error messages.
        """
        errors = [
            f"Invalid output number {accessory.output_number} for accessory '{accessory.name}'. Must be positive."
            for accessory in self.config.accessories
            if accessory.output_number < 0
        ]

        return errors

    def validate_unique_room_names(self) -> List[str]:
        """Validate that all room names are unique.

        Returns:
            List of validation error messages.
        """
        names: Set[str] = set()
        errors = []

        for room in self.config.bridge.rooms:
            if room.name in names:
                errors.append(f"Duplicate room name: {room.name}")
            names.add(room.name)

        return errors

    def validate_room_accessory_references(self) -> List[str]:
        """Validate that all room accessories exist in accessories section.

        Returns:
            List of validation error messages.
        """
        accessory_names = {acc.name for acc in self.config.accessories}
        errors = []

        for room in self.config.bridge.rooms:
            for acc_name in room.accessories:
                if acc_name not in accessory_names:
                    errors.append(
                        f"Room '{room.name}' references unknown accessory '{acc_name}'"
                    )

        return errors

    def validate_no_orphaned_accessories(self) -> List[str]:
        """Validate that all accessories are assigned to at least one room.

        Returns:
            List of validation error messages.
        """
        assigned_accessories: Set[str] = set()
        for room in self.config.bridge.rooms:
            assigned_accessories.update(room.accessories)

        errors = [
            f"Accessory '{accessory.name}' is not assigned to any room"
            for accessory in self.config.accessories
            if accessory.name not in assigned_accessories
        ]

        return errors

    def validate_no_duplicate_accessory_assignments(self) -> List[str]:
        """Validate that accessories are not assigned to multiple rooms.

        Returns:
            List of validation error messages.
        """
        assigned_accessories: Set[str] = set()
        errors = []

        for room in self.config.bridge.rooms:
            for acc_name in room.accessories:
                if acc_name in assigned_accessories:
                    errors.append(
                        f"Accessory '{acc_name}' is assigned to multiple rooms"
                    )
                assigned_accessories.add(acc_name)

        return errors

    def validate_all(self) -> List[str]:
        """Run all validations and return combined errors.

        Returns:
            List of all validation error messages.
        """
        all_errors = []
        all_errors.extend(self.validate_unique_accessory_names())
        all_errors.extend(self.validate_service_types())
        all_errors.extend(self.validate_output_numbers())
        all_errors.extend(self.validate_unique_room_names())
        all_errors.extend(self.validate_room_accessory_references())
        all_errors.extend(self.validate_no_orphaned_accessories())
        all_errors.extend(self.validate_no_duplicate_accessory_assignments())
        return all_errors


class CrossReferenceValidator:
    """Validates cross-references between conson.yml and homekit.yml configurations."""

    def __init__(
        self,
        conson_validator: ConsonConfigValidator,
        homekit_validator: HomekitConfigValidator,
    ):
        """Initialize the cross-reference validator.

        Args:
            conson_validator: Conson configuration validator.
            homekit_validator: HomeKit configuration validator.
        """
        self.conson_validator = conson_validator
        self.homekit_validator = homekit_validator

    def validate_serial_number_references(self) -> List[str]:
        """Validate that all accessory serial numbers exist in conson configuration.

        Returns:
            List of validation error messages.
        """
        conson_serials = self.conson_validator.get_all_serial_numbers()
        errors = [
            f"Accessory '{accessory.name}' references unknown serial number {accessory.serial_number}"
            for accessory in self.homekit_validator.config.accessories
            if accessory.serial_number not in conson_serials
        ]

        return errors

    def validate_output_capabilities(self) -> List[str]:
        """Validate that output numbers are within module capabilities.

        Returns:
            List of validation error messages.
        """
        errors = []

        for accessory in self.homekit_validator.config.accessories:
            with suppress(ValueError):
                module = self.conson_validator.get_module_by_serial(
                    accessory.serial_number
                )

                # Define output limits by module type
                output_limits = {
                    "XP130": 0,  # Example limits
                    "XP20": 0,
                    "XP24": 4,
                    "XP33": 3,
                    "XP33LR": 3,
                    "XP33LED": 3,
                    "XXP31LR": 1,
                    "XXP31CR": 1,
                    "XXP31BC": 1,
                    "XXP31LED": 1,
                }

                max_outputs = output_limits.get(module.module_type, 4)  # Default to 8

                if accessory.output_number > max_outputs:
                    errors.append(
                        f"Accessory '{accessory.name}' "
                        f"output {accessory.output_number} "
                        f"exceeds module '{module.name}' ({module.module_type}) "
                        f"limit of {max_outputs}"
                    )

        return errors

    def validate_all(self) -> List[str]:
        """Run all cross-reference validations and return combined errors.

        Returns:
            List of all cross-reference validation error messages.
        """
        all_errors = []
        all_errors.extend(self.validate_serial_number_references())
        all_errors.extend(self.validate_output_capabilities())
        return all_errors


class ConfigValidationService:
    """Main service for validating HomeKit configuration coherence."""

    def __init__(self, conson_config_path: str, homekit_config_path: str):
        """Initialize the config validation service.

        Args:
            conson_config_path: Path to conson.yml configuration file.
            homekit_config_path: Path to homekit.yml configuration file.
        """
        from xp.models.homekit.homekit_config import HomekitConfig
        from xp.models.homekit.homekit_conson_config import ConsonModuleListConfig

        self.conson_config = ConsonModuleListConfig.from_yaml(conson_config_path)
        self.homekit_config = HomekitConfig.from_yaml(homekit_config_path)

        self.conson_validator = ConsonConfigValidator(self.conson_config)
        self.homekit_validator = HomekitConfigValidator(self.homekit_config)
        self.cross_validator = CrossReferenceValidator(
            self.conson_validator, self.homekit_validator
        )

    def validate_all(self) -> dict:
        """Run all validations and return organized results.

        Returns:
            Dictionary containing validation results and error counts.
        """
        conson_errors = self.conson_validator.validate_all()
        homekit_errors = self.homekit_validator.validate_all()
        cross_errors = self.cross_validator.validate_all()

        return {
            "conson_errors": conson_errors,
            "homekit_errors": homekit_errors,
            "cross_reference_errors": cross_errors,
            "total_errors": len(conson_errors)
            + len(homekit_errors)
            + len(cross_errors),
            "is_valid": len(conson_errors) + len(homekit_errors) + len(cross_errors)
            == 0,
        }

    def print_config_summary(self) -> str:
        """Generate a summary of the configuration.

        Returns:
            String containing configuration summary.
        """
        summary = [
            f"Conson Modules: {len(self.conson_config.root)}",
            f"HomeKit Accessories: {len(self.homekit_config.accessories)}",
            f"HomeKit Rooms: {len(self.homekit_config.bridge.rooms)}",
        ]

        # Count accessories by service type
        service_counts: dict[str, int] = {}
        for acc in self.homekit_config.accessories:
            service_counts[acc.service] = service_counts.get(acc.service, 0) + 1

        summary.append("Service Types:")
        for service, count in service_counts.items():
            summary.append(f"  - {service}: {count}")

        return "\n".join(summary)

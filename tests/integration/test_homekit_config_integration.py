"""Integration tests for HomeKit configuration validation."""

import tempfile
from pathlib import Path
from typing import List

import pytest
import yaml

from xp.models.homekit.homekit_conson_config import ConsonModuleConfig
from xp.services.homekit.homekit_config_validator import ConfigValidationService


class TestHomekitConfigIntegration:
    """Integration tests for HomeKit configuration validation using temporary files."""

    @staticmethod
    def create_temp_conson_config(modules_data):
        """Create a temporary conson.yml file with the given module's data.

        Args:
            modules_data: Module data to write to the file.

        Returns:
            str: Path to the temporary file.
        """
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False)
        yaml.dump(modules_data, temp_file, default_flow_style=False)
        temp_file.close()
        return temp_file.name

    @staticmethod
    def create_temp_homekit_config(config_data):
        """Create a temporary homekit.yml file with the given config data.

        Args:
            config_data: Configuration data to write to the file.

        Returns:
            str: Path to the temporary file.
        """
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False)
        yaml.dump(config_data, temp_file, default_flow_style=False)
        temp_file.close()
        return temp_file.name

    @staticmethod
    def cleanup_temp_files(*file_paths):
        """Clean up temporary files.

        Args:
            file_paths: Variable number of file paths to clean up.
        """
        for file_path in file_paths:
            if Path(file_path).exists():
                Path(file_path).unlink()

    def test_valid_configuration_integration(self):
        """Test complete validation with valid configuration files."""
        # Create valid conson configuration
        conson_data = [
            {
                "name": "ModuleA",
                "serial_number": "1234567890",
                "module_type": "XP24",
                "module_type_code": 13,
                "link_number": 1,
                "module_number": 1,
                "conbus_ip": "192.168.1.100",
                "conbus_port": 10001,
                "sw_version": "XP130_V0.10.04",
                "hw_version": "XP130_HW_Rev B",
            },
            {
                "name": "ModuleB",
                "serial_number": "9876543210",
                "module_type": "XP24",
                "module_type_code": 20,
                "link_number": 2,
                "module_number": 2,
                "conbus_ip": "192.168.1.101",
                "conbus_port": 10002,
            },
        ]

        # Create valid homekit configuration
        homekit_data = {
            "homekit": {"ip": "192.168.1.50", "port": 51827},
            "conson": {"ip": "192.168.1.200", "port": 10001},
            "bridge": {
                "name": "Test Home",
                "rooms": [
                    {"name": "Living Room", "accessories": ["main_light", "side_lamp"]},
                    {"name": "Kitchen", "accessories": ["kitchen_light"]},
                ],
            },
            "accessories": [
                {
                    "name": "main_light",
                    "id": "A1R1",
                    "serial_number": "1234567890",
                    "output_number": 1,
                    "description": "Main Living Room Light",
                    "service": "lightbulb",
                    "on_action": "E00L01I01",
                    "off_action": "E00L01I05",
                },
                {
                    "name": "side_lamp",
                    "id": "A1R2",
                    "serial_number": "1234567890",
                    "output_number": 2,
                    "description": "Side Lamp",
                    "service": "lightbulb",
                    "on_action": "E00L01I02",
                    "off_action": "E00L01I06",
                },
                {
                    "name": "kitchen_light",
                    "id": "A2R1",
                    "serial_number": "9876543210",
                    "output_number": 1,
                    "description": "Kitchen Light",
                    "service": "lightbulb",
                    "on_action": "E00L02I01",
                    "off_action": "E00L02I05",
                },
            ],
        }

        conson_file = self.create_temp_conson_config(conson_data)
        homekit_file = self.create_temp_homekit_config(homekit_data)

        try:
            validator = ConfigValidationService(conson_file, homekit_file)
            results = validator.validate_all()

            assert results["is_valid"] is True
            assert results["total_errors"] == 0
            assert results["conson_errors"] == []
            assert results["homekit_errors"] == []
            assert results["cross_reference_errors"] == []

            # Test configuration summary
            summary = validator.print_config_summary()
            assert "Conson Modules: 2" in summary
            assert "HomeKit Accessories: 3" in summary
            assert "HomeKit Rooms: 2" in summary
            assert "lightbulb: 3" in summary

        finally:
            self.cleanup_temp_files(conson_file, homekit_file)

    def test_invalid_configuration_integration(self):
        """Test complete validation with invalid configuration files."""
        # Create invalid conson configuration (duplicate names and serials)
        conson_data = [
            {
                "name": "DuplicateModule",
                "serial_number": "1234567890",
                "module_type": "XP130",
                "module_type_code": 13,
                "link_number": 1,
            },
            {
                "name": "DuplicateModule",  # Duplicate name
                "serial_number": "1234567890",  # Duplicate serial
                "module_type": "XP20",
                "module_type_code": 300,  # Invalid type code
                "link_number": 2,
                "conbus_port": 80000,  # Invalid port
            },
        ]

        # Create invalid homekit configuration
        homekit_data = {
            "homekit": {"ip": "192.168.1.50", "port": 51827},
            "conson": {"ip": "192.168.1.200", "port": 10001},
            "bridge": {
                "name": "Test Home",
                "rooms": [
                    {
                        "name": "Living Room",
                        "accessories": [
                            "main_light",
                            "nonexistent_light",
                        ],  # Non-existent accessory
                    },
                    {
                        "name": "Living Room",  # Duplicate room name
                        "accessories": ["side_lamp"],
                    },
                ],
            },
            "accessories": [
                {
                    "name": "main_light",
                    "id": "A1R1",
                    "serial_number": "9999999999",  # Non-existent serial
                    "output_number": 0,  # Invalid output
                    "description": "Main Light",
                    "service": "invalid_service",  # Invalid service
                    "on_action": "E00L01I01",
                    "off_action": "E00L01I05",
                },
                {
                    "name": "main_light",  # Duplicate accessory name
                    "id": "A1R2",
                    "serial_number": "1234567890",
                    "output_number": 50,  # Output exceeds module capability
                    "description": "Duplicate Light",
                    "service": "lightbulb",
                    "on_action": "E00L01I02",
                    "off_action": "E00L01I06",
                },
                {
                    "name": "orphaned_light",  # Not assigned to any room
                    "id": "A1R3",
                    "serial_number": "1234567890",
                    "output_number": 3,
                    "description": "Orphaned Light",
                    "service": "lightbulb",
                    "on_action": "E00L01I03",
                    "off_action": "E00L01I07",
                },
            ],
        }

        conson_file = self.create_temp_conson_config(conson_data)
        homekit_file = self.create_temp_homekit_config(homekit_data)

        try:
            validator = ConfigValidationService(conson_file, homekit_file)
            results = validator.validate_all()

            assert results["is_valid"] is False
            assert results["total_errors"] > 0

            # Check that we have errors in all categories
            assert len(results["conson_errors"]) > 0
            assert len(results["homekit_errors"]) > 0
            assert len(results["cross_reference_errors"]) > 0

            # Verify specific error types
            conson_errors_str = " ".join(results["conson_errors"])
            assert "Duplicate module name" in conson_errors_str
            assert "Duplicate serial number" in conson_errors_str
            assert "Invalid module_type_code" in conson_errors_str
            assert "Invalid conbus_port" in conson_errors_str

            homekit_errors_str = " ".join(results["homekit_errors"])
            assert "Duplicate accessory name" in homekit_errors_str
            assert "Duplicate room name" in homekit_errors_str
            assert "references unknown accessory" in homekit_errors_str
            assert "Invalid service type" in homekit_errors_str
            assert "not assigned to any room" in homekit_errors_str

            cross_errors_str = " ".join(results["cross_reference_errors"])
            assert "references unknown serial number" in cross_errors_str
            assert "output" in cross_errors_str and "exceeds module" in cross_errors_str

        finally:
            self.cleanup_temp_files(conson_file, homekit_file)

    def test_malformed_yaml_integration(self):
        """Test behavior with malformed YAML files."""
        # Create malformed conson YAML
        malformed_conson = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        )
        malformed_conson.write("invalid: yaml: content: [unclosed")
        malformed_conson.close()

        # Create valid homekit YAML
        homekit_data = {
            "homekit": {"ip": "192.168.1.50", "port": 51827},
            "conson": {"ip": "192.168.1.200", "port": 10001},
            "bridge": {"name": "Test", "rooms": []},
            "accessories": [],
        }
        homekit_file = self.create_temp_homekit_config(homekit_data)

        try:
            with pytest.raises(yaml.YAMLError):
                ConfigValidationService(malformed_conson.name, homekit_file)
        finally:
            self.cleanup_temp_files(malformed_conson.name, homekit_file)

    def test_empty_configuration_integration(self):
        """Test validation with empty but valid configuration files."""
        conson_data: List[ConsonModuleConfig] = []
        homekit_data = {
            "homekit": {"ip": "192.168.1.50", "port": 51827},
            "conson": {"ip": "192.168.1.200", "port": 10001},
            "bridge": {"name": "Empty Home", "rooms": []},
            "accessories": [],
        }

        conson_file = self.create_temp_conson_config(conson_data)
        homekit_file = self.create_temp_homekit_config(homekit_data)

        try:
            validator = ConfigValidationService(conson_file, homekit_file)
            results = validator.validate_all()

            assert results["is_valid"] is True
            assert results["total_errors"] == 0

            summary = validator.print_config_summary()
            assert "Conson Modules: 0" in summary
            assert "HomeKit Accessories: 0" in summary
            assert "HomeKit Rooms: 0" in summary

        finally:
            self.cleanup_temp_files(conson_file, homekit_file)

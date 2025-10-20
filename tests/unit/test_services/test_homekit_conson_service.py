"""Unit tests for HomeKit Conson service."""

import pytest

from xp.models.homekit.homekit_conson_config import (
    ConsonModuleConfig,
    ConsonModuleListConfig,
)
from xp.services.homekit.homekit_conson_validator import ConsonConfigValidator


class TestConsonConfigValidator:
    """Test cases for ConsonConfigValidator."""

    def test_validate_unique_names_success(self):
        """Test validation passes when all module names are unique."""
        modules = [
            ConsonModuleConfig(
                name="A1",
                serial_number="123",
                module_type="XP130",
                module_type_code=13,
                link_number=1,
            ),
            ConsonModuleConfig(
                name="A2",
                serial_number="456",
                module_type="XP20",
                module_type_code=20,
                link_number=2,
            ),
        ]
        config = ConsonModuleListConfig(root=modules)
        errors = ConsonConfigValidator(config).validate_unique_names()
        assert errors == []

    def test_validate_unique_names_failure(self):
        """Test validation fails when module names are duplicated."""
        modules = [
            ConsonModuleConfig(
                name="A1",
                serial_number="123",
                module_type="XP130",
                module_type_code=13,
                link_number=1,
            ),
            ConsonModuleConfig(
                name="A1",
                serial_number="456",
                module_type="XP20",
                module_type_code=20,
                link_number=2,
            ),
        ]
        config = ConsonModuleListConfig(root=modules)
        errors = ConsonConfigValidator(config).validate_unique_names()
        assert len(errors) == 1
        assert "Duplicate module name: A1" in errors[0]

    def test_validate_unique_serial_numbers_success(self):
        """Test validation passes when all serial numbers are unique."""
        modules = [
            ConsonModuleConfig(
                name="A1",
                serial_number="123",
                module_type="XP130",
                module_type_code=13,
                link_number=1,
            ),
            ConsonModuleConfig(
                name="A2",
                serial_number="456",
                module_type="XP20",
                module_type_code=20,
                link_number=2,
            ),
        ]
        config = ConsonModuleListConfig(root=modules)
        errors = ConsonConfigValidator(config).validate_unique_serial_numbers()
        assert errors == []

    def test_validate_unique_serial_numbers_failure(self):
        """Test validation fails when serial numbers are duplicated."""
        modules = [
            ConsonModuleConfig(
                name="A1",
                serial_number="123",
                module_type="XP130",
                module_type_code=13,
                link_number=1,
            ),
            ConsonModuleConfig(
                name="A2",
                serial_number="123",
                module_type="XP20",
                module_type_code=20,
                link_number=2,
            ),
        ]
        config = ConsonModuleListConfig(root=modules)
        errors = ConsonConfigValidator(config).validate_unique_serial_numbers()
        assert len(errors) == 1
        assert "Duplicate serial number: 123" in errors[0]

    def test_validate_module_type_codes_success(self):
        """Test validation passes for valid module type codes."""
        modules = [
            ConsonModuleConfig(
                name="A1",
                serial_number="123",
                module_type="XP130",
                module_type_code=13,
                link_number=1,
            ),
            ConsonModuleConfig(
                name="A2",
                serial_number="456",
                module_type="XP20",
                module_type_code=255,
                link_number=2,
            ),
        ]
        config = ConsonModuleListConfig(root=modules)
        errors = ConsonConfigValidator(config).validate_module_type_codes()
        assert errors == []

    def test_validate_module_type_codes_failure(self):
        """Test validation fails for invalid module type codes."""
        modules = [
            ConsonModuleConfig(
                name="A1",
                serial_number="123",
                module_type="XP130",
                module_type_code=0,
                link_number=1,
            ),
            ConsonModuleConfig(
                name="A2",
                serial_number="456",
                module_type="XP20",
                module_type_code=256,
                link_number=2,
            ),
        ]
        config = ConsonModuleListConfig(root=modules)
        errors = ConsonConfigValidator(config).validate_module_type_codes()
        assert len(errors) == 2
        assert "Invalid module_type_code 0" in errors[0]
        assert "Invalid module_type_code 256" in errors[1]

    def test_validate_network_config_success(self):
        """Test validation passes for valid network configuration."""
        modules = [
            ConsonModuleConfig(
                name="A1",
                serial_number="123",
                module_type="XP130",
                module_type_code=13,
                link_number=1,
                conbus_port=10001,
            ),
        ]
        config = ConsonModuleListConfig(root=modules)
        errors = ConsonConfigValidator(config).validate_network_config()
        assert errors == []

    def test_validate_network_config_failure(self):
        """Test validation fails for invalid network configuration."""
        modules = [
            ConsonModuleConfig(
                name="A1",
                serial_number="123",
                module_type="XP130",
                module_type_code=13,
                link_number=1,
                conbus_port=0,
            ),
            ConsonModuleConfig(
                name="A2",
                serial_number="456",
                module_type="XP20",
                module_type_code=20,
                link_number=2,
                conbus_port=70000,
            ),
        ]
        config = ConsonModuleListConfig(root=modules)
        errors = ConsonConfigValidator(config).validate_network_config()
        assert len(errors) == 2
        assert "Invalid conbus_port 0" in errors[0]
        assert "Invalid conbus_port 70000" in errors[1]

    def test_get_module_by_serial_success(self):
        """Test getting module by serial number."""
        modules = [
            ConsonModuleConfig(
                name="A1",
                serial_number="123",
                module_type="XP130",
                module_type_code=13,
                link_number=1,
            ),
        ]
        config = ConsonModuleListConfig(root=modules)
        module = ConsonConfigValidator(config).get_module_by_serial("123")
        assert module.name == "A1"
        assert module.module_type == "XP130"

    def test_get_module_by_serial_not_found(self):
        """Test getting module by non-existent serial number."""
        modules = [
            ConsonModuleConfig(
                name="A1",
                serial_number="123",
                module_type="XP130",
                module_type_code=13,
                link_number=1,
            ),
        ]
        config = ConsonModuleListConfig(root=modules)
        validator = ConsonConfigValidator(config)

        with pytest.raises(ValueError, match="Module with serial number 999 not found"):
            validator.get_module_by_serial("999")

    def test_get_all_serial_numbers(self):
        """Test getting all serial numbers from configuration."""
        modules = [
            ConsonModuleConfig(
                name="A1",
                serial_number="123",
                module_type="XP130",
                module_type_code=13,
                link_number=1,
            ),
            ConsonModuleConfig(
                name="A2",
                serial_number="456",
                module_type="XP20",
                module_type_code=20,
                link_number=2,
            ),
        ]
        config = ConsonModuleListConfig(root=modules)
        serials = ConsonConfigValidator(config).get_all_serial_numbers()
        assert serials == {"123", "456"}

    def test_validate_all_success(self):
        """Test that validate_all returns no errors for valid configuration."""
        modules = [
            ConsonModuleConfig(
                name="A1",
                serial_number="123",
                module_type="XP130",
                module_type_code=13,
                link_number=1,
                conbus_port=10001,
            ),
            ConsonModuleConfig(
                name="A2",
                serial_number="456",
                module_type="XP20",
                module_type_code=20,
                link_number=2,
                conbus_port=10002,
            ),
        ]
        config = ConsonModuleListConfig(root=modules)
        errors = ConsonConfigValidator(config).validate_all()
        assert errors == []

    def test_validate_all_with_errors(self):
        """Test that validate_all returns all errors for invalid configuration."""
        modules = [
            ConsonModuleConfig(
                name="A1",
                serial_number="123",
                module_type="XP130",
                module_type_code=0,
                link_number=1,
                conbus_port=0,
            ),
            ConsonModuleConfig(
                name="A1",
                serial_number="123",
                module_type="XP20",
                module_type_code=256,
                link_number=2,
                conbus_port=70000,
            ),
        ]
        config = ConsonModuleListConfig(root=modules)
        errors = ConsonConfigValidator(config).validate_all()
        assert len(errors) > 0
        # Should have duplicate name, duplicate serial, invalid type codes, and invalid ports
        assert any("Duplicate module name" in error for error in errors)
        assert any("Duplicate serial number" in error for error in errors)
        assert any("Invalid module_type_code" in error for error in errors)
        assert any("Invalid conbus_port" in error for error in errors)

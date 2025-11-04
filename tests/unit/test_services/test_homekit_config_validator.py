"""Unit tests for HomeKit configuration validator."""

from xp.models.homekit.homekit_config import (
    BridgeConfig,
    HomekitAccessoryConfig,
    HomekitConfig,
    NetworkConfig,
    RoomConfig,
)
from xp.models.homekit.homekit_conson_config import (
    ConsonModuleConfig,
    ConsonModuleListConfig,
)
from xp.services.homekit.homekit_config_validator import (
    CrossReferenceValidator,
    HomekitConfigValidator,
)
from xp.services.homekit.homekit_conson_validator import ConsonConfigValidator


class TestHomekitConfigValidator:
    """Test cases for HomekitConfigValidator."""

    @staticmethod
    def create_test_homekit_config(accessories=None, rooms=None):
        """Create test HomeKit configuration.

        Args:
            accessories: Optional list of accessory configurations.
            rooms: Optional list of room configurations.

        Returns:
            HomekitConfig: A configured HomeKit config object for testing.
        """
        if accessories is None:
            accessories = [
                HomekitAccessoryConfig(
                    name="light1",
                    id="A1R1",
                    serial_number="123",
                    output_number=1,
                    description="Light 1",
                    service="lightbulb",
                    on_action="E00L01I01",
                    off_action="E00L01I05",
                ),
                HomekitAccessoryConfig(
                    name="light2",
                    id="A1R2",
                    serial_number="123",
                    output_number=2,
                    description="Light 2",
                    service="lightbulb",
                    on_action="E00L01I02",
                    off_action="E00L01I06",
                ),
            ]

        if rooms is None:
            rooms = [RoomConfig(name="Living Room", accessories=["light1", "light2"])]

        bridge = BridgeConfig(name="Test Bridge", rooms=rooms)
        homekit_net = NetworkConfig(ip="192.168.1.100", port=51827)
        conson_net = NetworkConfig(ip="192.168.1.200", port=10001)

        return HomekitConfig(
            homekit=homekit_net,
            conson=conson_net,
            bridge=bridge,
            accessories=accessories,
        )

    def test_validate_unique_accessory_names_success(self):
        """Test validation passes when all accessory names are unique."""
        config = self.create_test_homekit_config()
        errors = HomekitConfigValidator(config).validate_unique_accessory_names()
        assert errors == []

    def test_validate_unique_accessory_names_failure(self):
        """Test validation fails when accessory names are duplicated."""
        accessories = [
            HomekitAccessoryConfig(
                name="light1",
                id="A1R1",
                serial_number="123",
                output_number=1,
                description="Light 1",
                service="lightbulb",
                on_action="E00L01I01",
                off_action="E00L01I05",
            ),
            HomekitAccessoryConfig(
                name="light1",
                id="A1R2",
                serial_number="123",
                output_number=2,
                description="Light 2",
                service="lightbulb",
                on_action="E00L01I02",
                off_action="E00L01I06",
            ),
        ]
        config = self.create_test_homekit_config(accessories=accessories)
        errors = HomekitConfigValidator(config).validate_unique_accessory_names()
        assert len(errors) == 1
        assert "Duplicate accessory name: light1" in errors[0]

    def test_validate_service_types_success(self):
        """Test validation passes for valid service types."""
        config = self.create_test_homekit_config()
        errors = HomekitConfigValidator(config).validate_service_types()
        assert errors == []

    def test_validate_service_types_failure(self):
        """Test validation fails for invalid service types."""
        accessories = [
            HomekitAccessoryConfig(
                name="light1",
                id="A1R1",
                serial_number="123",
                output_number=1,
                description="Light 1",
                service="invalid_service",
                on_action="E00L01I01",
                off_action="E00L01I05",
            )
        ]
        config = self.create_test_homekit_config(accessories=accessories)
        errors = HomekitConfigValidator(config).validate_service_types()
        assert len(errors) == 1
        assert "Invalid service type 'invalid_service'" in errors[0]

    def test_validate_output_numbers_success(self):
        """Test validation passes for valid output numbers."""
        config = self.create_test_homekit_config()
        errors = HomekitConfigValidator(config).validate_output_numbers()
        assert errors == []

    def test_validate_output_numbers_failure(self):
        """Test validation fails for invalid output numbers."""
        accessories = [
            HomekitAccessoryConfig(
                name="light1",
                id="A1R1",
                serial_number="123",
                output_number=0,
                description="Light 1",
                service="lightbulb",
                on_action="E00L01I01",
                off_action="E00L01I05",
            ),
            HomekitAccessoryConfig(
                name="light2",
                id="A1R2",
                serial_number="123",
                output_number=-1,
                description="Light 2",
                service="lightbulb",
                on_action="E00L01I02",
                off_action="E00L01I06",
            ),
        ]
        config = self.create_test_homekit_config(accessories=accessories)
        errors = HomekitConfigValidator(config).validate_output_numbers()
        assert len(errors) == 1
        assert "Invalid output number -1" in errors[0]

    def test_validate_unique_room_names_success(self):
        """Test validation passes when all room names are unique."""
        rooms = [
            RoomConfig(name="Living Room", accessories=["light1"]),
            RoomConfig(name="Kitchen", accessories=["light2"]),
        ]
        config = self.create_test_homekit_config(rooms=rooms)
        errors = HomekitConfigValidator(config).validate_unique_room_names()
        assert errors == []

    def test_validate_unique_room_names_failure(self):
        """Test validation fails when room names are duplicated."""
        rooms = [
            RoomConfig(name="Living Room", accessories=["light1"]),
            RoomConfig(name="Living Room", accessories=["light2"]),
        ]
        config = self.create_test_homekit_config(rooms=rooms)
        errors = HomekitConfigValidator(config).validate_unique_room_names()
        assert len(errors) == 1
        assert "Duplicate room name: Living Room" in errors[0]

    def test_validate_room_accessory_references_success(self):
        """Test validation passes when all room accessories exist."""
        config = self.create_test_homekit_config()
        errors = HomekitConfigValidator(config).validate_room_accessory_references()
        assert errors == []

    def test_validate_room_accessory_references_failure(self):
        """Test validation fails when room references non-existent accessories."""
        rooms = [
            RoomConfig(name="Living Room", accessories=["light1", "nonexistent_light"])
        ]
        config = self.create_test_homekit_config(rooms=rooms)
        errors = HomekitConfigValidator(config).validate_room_accessory_references()
        assert len(errors) == 1
        assert (
            "Room 'Living Room' references unknown accessory 'nonexistent_light'"
            in errors[0]
        )

    def test_validate_no_orphaned_accessories_success(self):
        """Test validation passes when all accessories are assigned to rooms."""
        config = self.create_test_homekit_config()
        errors = HomekitConfigValidator(config).validate_no_orphaned_accessories()
        assert errors == []

    def test_validate_no_orphaned_accessories_failure(self):
        """Test validation fails when accessories are not assigned to any room."""
        accessories = [
            HomekitAccessoryConfig(
                name="light1",
                id="A1R1",
                serial_number="123",
                output_number=1,
                description="Light 1",
                service="lightbulb",
                on_action="E00L01I01",
                off_action="E00L01I05",
            ),
            HomekitAccessoryConfig(
                name="orphaned_light",
                id="A1R2",
                serial_number="123",
                output_number=2,
                description="Orphaned",
                service="lightbulb",
                on_action="E00L01I02",
                off_action="E00L01I06",
            ),
        ]
        rooms = [RoomConfig(name="Living Room", accessories=["light1"])]
        config = self.create_test_homekit_config(accessories=accessories, rooms=rooms)
        errors = HomekitConfigValidator(config).validate_no_orphaned_accessories()
        assert len(errors) == 1
        assert "Accessory 'orphaned_light' is not assigned to any room" in errors[0]

    def test_validate_no_duplicate_accessory_assignments_success(self):
        """Test validation passes when accessories are not assigned to multiple rooms."""
        accessories = [
            HomekitAccessoryConfig(
                name="light1",
                id="A1R1",
                serial_number="123",
                output_number=1,
                description="Light 1",
                service="lightbulb",
                on_action="E00L01I01",
                off_action="E00L01I05",
            ),
            HomekitAccessoryConfig(
                name="light2",
                id="A1R2",
                serial_number="123",
                output_number=2,
                description="Light 2",
                service="lightbulb",
                on_action="E00L01I02",
                off_action="E00L01I06",
            ),
        ]
        rooms = [
            RoomConfig(name="Living Room", accessories=["light1"]),
            RoomConfig(name="Kitchen", accessories=["light2"]),
        ]
        config = self.create_test_homekit_config(accessories=accessories, rooms=rooms)
        errors = HomekitConfigValidator(
            config
        ).validate_no_duplicate_accessory_assignments()
        assert errors == []

    def test_validate_no_duplicate_accessory_assignments_failure(self):
        """Test validation fails when accessories are assigned to multiple rooms."""
        accessories = [
            HomekitAccessoryConfig(
                name="light1",
                id="A1R1",
                serial_number="123",
                output_number=1,
                description="Light 1",
                service="lightbulb",
                on_action="E00L01I01",
                off_action="E00L01I05",
            )
        ]
        rooms = [
            RoomConfig(name="Living Room", accessories=["light1"]),
            RoomConfig(name="Kitchen", accessories=["light1"]),
        ]
        config = self.create_test_homekit_config(accessories=accessories, rooms=rooms)
        errors = HomekitConfigValidator(
            config
        ).validate_no_duplicate_accessory_assignments()
        assert len(errors) == 1
        assert "Accessory 'light1' is assigned to multiple rooms" in errors[0]


class TestCrossReferenceValidator:
    """Test cases for CrossReferenceValidator."""

    @staticmethod
    def create_test_validators():
        """Create test validators with compatible configurations.

        Returns:
            tuple: A tuple of (HomeKit validator, Conson validator) for testing.
        """
        # Create conson config
        conson_modules = [
            ConsonModuleConfig(
                name="Module1",
                serial_number="123",
                module_type="XP24",
                module_type_code=13,
                link_number=1,
            ),
            ConsonModuleConfig(
                name="Module2",
                serial_number="456",
                module_type="XP31LED",
                module_type_code=20,
                link_number=2,
            ),
        ]
        conson_config = ConsonModuleListConfig(root=conson_modules)
        conson_validator = ConsonConfigValidator(conson_config)

        # Create homekit config
        accessories = [
            HomekitAccessoryConfig(
                name="light1",
                id="A1R1",
                serial_number="123",
                output_number=1,
                description="Light 1",
                service="lightbulb",
                on_action="E00L01I01",
                off_action="E00L01I05",
            ),
            HomekitAccessoryConfig(
                name="light2",
                id="A1R2",
                serial_number="456",
                output_number=1,
                description="Light 2",
                service="lightbulb",
                on_action="E00L02I01",
                off_action="E00L02I05",
            ),
        ]
        rooms = [RoomConfig(name="Living Room", accessories=["light1", "light2"])]
        bridge = BridgeConfig(name="Test Bridge", rooms=rooms)
        homekit_net = NetworkConfig(ip="192.168.1.100", port=51827)
        conson_net = NetworkConfig(ip="192.168.1.200", port=10001)

        homekit_config = HomekitConfig(
            homekit=homekit_net,
            conson=conson_net,
            bridge=bridge,
            accessories=accessories,
        )
        homekit_validator = HomekitConfigValidator(homekit_config)

        return conson_validator, homekit_validator

    def test_validate_serial_number_references_success(self):
        """Test validation passes when all accessory serial numbers exist in conson config."""
        conson_validator, homekit_validator = self.create_test_validators()
        errors = CrossReferenceValidator(
            conson_validator, homekit_validator
        ).validate_serial_number_references()
        assert errors == []

    def test_validate_serial_number_references_failure(self):
        """Test validation fails when accessory references non-existent serial number."""
        conson_validator, homekit_validator = self.create_test_validators()

        # Add accessory with non-existent serial number
        invalid_accessory = HomekitAccessoryConfig(
            name="invalid_light",
            id="A1R3",
            serial_number="999",
            output_number=1,
            description="Invalid",
            service="lightbulb",
            on_action="E00L03I01",
            off_action="E00L03I05",
        )
        homekit_validator.config.accessories.append(invalid_accessory)

        errors = CrossReferenceValidator(
            conson_validator, homekit_validator
        ).validate_serial_number_references()

        assert len(errors) == 1
        assert (
            "Accessory 'invalid_light' references unknown serial number 999"
            in errors[0]
        )

    def test_validate_output_capabilities_success(self):
        """Test validation passes when output numbers are within module capabilities."""
        conson_validator, homekit_validator = self.create_test_validators()
        errors = CrossReferenceValidator(
            conson_validator, homekit_validator
        ).validate_output_capabilities()
        assert errors == []

    def test_validate_output_capabilities_failure(self):
        """Test validation fails when output numbers exceed module capabilities."""
        conson_validator, homekit_validator = self.create_test_validators()

        # Add accessory with output exceeding XP20 module limit (8)
        high_output_accessory = HomekitAccessoryConfig(
            name="high_output",
            id="A2R9",
            serial_number="456",
            output_number=20,
            description="High Output",
            service="lightbulb",
            on_action="E00L02I09",
            off_action="E00L02I13",
        )
        homekit_validator.config.accessories.append(high_output_accessory)

        errors = CrossReferenceValidator(
            conson_validator, homekit_validator
        ).validate_output_capabilities()

        assert len(errors) == 1
        assert "output 20 exceeds module" in errors[0]

    def test_validate_all_success(self):
        """Test that validate_all returns no errors for valid cross-references."""
        conson_validator, homekit_validator = self.create_test_validators()
        errors = CrossReferenceValidator(
            conson_validator, homekit_validator
        ).validate_all()
        assert errors == []

    def test_validate_all_with_errors(self):
        """Test that validate_all returns all cross-reference errors."""
        conson_validator, homekit_validator = self.create_test_validators()

        # Add accessories with various issues
        invalid_accessories = [
            HomekitAccessoryConfig(
                name="invalid_serial",
                id="A1R3",
                serial_number="999",
                output_number=1,
                description="Invalid Serial",
                service="lightbulb",
                on_action="E00L03I01",
                off_action="E00L03I05",
            ),
            HomekitAccessoryConfig(
                name="invalid_output",
                id="A2R9",
                serial_number="456",
                output_number=20,
                description="Invalid Output",
                service="lightbulb",
                on_action="E00L02I09",
                off_action="E00L02I13",
            ),
        ]
        homekit_validator.config.accessories.extend(invalid_accessories)

        errors = CrossReferenceValidator(
            conson_validator, homekit_validator
        ).validate_all()

        assert len(errors) == 2
        assert any("output 20 exceeds module" in error for error in errors)

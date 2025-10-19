"""Unit tests for module type models."""

from xp.models.telegram.module_type import (
    ModuleType,
    get_all_module_types,
    get_module_types_by_category,
    is_valid_module_code,
)
from xp.models.telegram.module_type_code import MODULE_TYPE_REGISTRY


class TestModuleType:
    """Test cases for ModuleType model."""

    def test_create_module_type_from_valid_code(self):
        """Test creating ModuleType from valid code."""
        module = ModuleType.from_code(14)

        assert module is not None
        assert module.code == 14
        assert module.name == "XP2606"
        assert module.description == "5 way push button panel with sesam, L-Team design"

    def test_create_module_type_from_invalid_code(self):
        """Test creating ModuleType from invalid code returns None."""
        module = ModuleType.from_code(999)
        assert module is None

    def test_create_module_type_from_valid_name(self):
        """Test creating ModuleType from valid name."""
        module = ModuleType.from_name("XP2606")

        assert module is not None
        assert module.code == 14
        assert module.name == "XP2606"
        assert module.description == "5 way push button panel with sesam, L-Team design"

    def test_create_module_type_from_valid_name_case_insensitive(self):
        """Test creating ModuleType from name is case-insensitive."""
        module = ModuleType.from_name("xp2606")
        assert module is not None
        assert module.name == "XP2606"

        module = ModuleType.from_name("Xp2606")
        assert module is not None
        assert module.name == "XP2606"

    def test_create_module_type_from_invalid_name(self):
        """Test creating ModuleType from invalid name returns None."""
        module = ModuleType.from_name("INVALID")
        assert module is None

    def test_is_reserved_property(self):
        """Test is_reserved property."""
        reserved1 = ModuleType.from_code(17)  # XP26X1
        reserved2 = ModuleType.from_code(18)  # XP26X2
        not_reserved = ModuleType.from_code(14)  # XP2606

        assert reserved1 is not None
        assert reserved2 is not None
        assert not_reserved is not None

        assert reserved1.is_reserved is True
        assert reserved2.is_reserved is True
        assert not_reserved.is_reserved is False

    def test_is_push_button_panel_property(self):
        """Test is_push_button_panel property."""
        panel1 = ModuleType.from_code(14)  # XP2606
        panel2 = ModuleType.from_code(19)  # XP2506
        panel3 = ModuleType.from_code(22)  # XPX1_8
        not_panel = ModuleType.from_code(7)  # XP24

        assert panel1 is not None
        assert panel2 is not None
        assert panel3 is not None
        assert not_panel is not None

        assert panel1.is_push_button_panel is True
        assert panel2.is_push_button_panel is True
        assert panel3.is_push_button_panel is True
        assert not_panel.is_push_button_panel is False

    def test_is_ir_capable_property(self):
        """Test is_ir_capable property."""
        ir_capable1 = ModuleType.from_code(3)  # CP70A (38kHz)
        ir_capable2 = ModuleType.from_code(4)  # CP70B (B&O)
        ir_capable3 = ModuleType.from_code(15)  # XP2606A
        not_ir_capable = ModuleType.from_code(14)  # XP2606

        assert ir_capable1 is not None
        assert ir_capable2 is not None
        assert ir_capable3 is not None
        assert not_ir_capable is not None

        assert ir_capable1.is_ir_capable is True
        assert ir_capable2.is_ir_capable is True
        assert ir_capable3.is_ir_capable is True
        assert not_ir_capable.is_ir_capable is False

    def test_category_property(self):
        """Test category property."""
        system_module = ModuleType.from_code(0)  # NOMOD - System
        cp_module = ModuleType.from_code(2)  # CP20 - CP Link Modules
        xp_module = ModuleType.from_code(7)  # XP24 - XP Control Modules
        interface_module = ModuleType.from_code(14)  # XP2606 - Interface Panels

        assert system_module is not None
        assert cp_module is not None
        assert xp_module is not None
        assert interface_module is not None

        assert system_module.category == "System"
        assert cp_module.category == "CP Link Modules"
        assert xp_module.category == "XP Control Modules"
        assert interface_module.category == "Interface Panels"

    def test_to_dict(self):
        """Test dictionary serialization."""
        module = ModuleType.from_code(14)  # XP2606

        assert module is not None
        result = module.to_dict()

        expected_keys = {
            "code",
            "name",
            "description",
            "category",
            "is_reserved",
            "is_push_button_panel",
            "is_ir_capable",
        }
        assert set(result.keys()) == expected_keys

        assert result["code"] == 14
        assert result["name"] == "XP2606"
        assert result["category"] == "Interface Panels"
        assert result["is_push_button_panel"] is True
        assert result["is_reserved"] is False
        assert result["is_ir_capable"] is False

    def test_str_representation(self):
        """Test human-readable string representation."""
        module = ModuleType.from_code(14)
        expected = "XP2606 (Code 14): 5 way push button panel with sesam, L-Team design"
        assert str(module) == expected

    def test_all_module_codes_covered(self):
        """Test that all codes in enum are in registry."""
        for code in range(25):  # 0-24 are defined in the spec including XP230
            assert code in MODULE_TYPE_REGISTRY

    def test_module_registry_completeness(self):
        """Test that module registry contains all expected entries."""
        assert len(MODULE_TYPE_REGISTRY) == 37

        # Test some specific entries
        assert MODULE_TYPE_REGISTRY[0]["name"] == "NOMOD"
        assert MODULE_TYPE_REGISTRY[7]["name"] == "XP24"
        assert MODULE_TYPE_REGISTRY[14]["name"] == "XP2606"
        assert MODULE_TYPE_REGISTRY[23]["name"] == "XP134"
        assert MODULE_TYPE_REGISTRY[24]["name"] == "XP24P"


class TestModuleTypeFunctions:
    """Test cases for module type utility functions."""

    def test_get_all_module_types(self):
        """Test getting all module types."""
        modules = get_all_module_types()

        assert len(modules) == 37
        assert all(isinstance(module, ModuleType) for module in modules)

        # Verify they are sorted by code
        codes = [module.code for module in modules]
        assert codes == sorted(codes)

    def test_get_module_types_by_category(self):
        """Test getting module types grouped by category."""
        categories = get_module_types_by_category()

        expected_categories = {
            "System",
            "CP Link Modules",
            "XP Control Modules",
            "Interface Panels",
            "Unknown",
        }
        assert set(categories.keys()) == expected_categories

        # Check some category contents
        system_modules = categories["System"]
        assert len(system_modules) == 2  # NOMOD and ALLMOD
        assert any(m.name == "NOMOD" for m in system_modules)
        assert any(m.name == "ALLMOD" for m in system_modules)

    def test_is_valid_module_code(self):
        """Test module code validation."""
        # Valid codes
        assert is_valid_module_code(0) is True
        assert is_valid_module_code(14) is True
        assert is_valid_module_code(23) is True
        assert is_valid_module_code(36) is True
        assert is_valid_module_code(37) is False

        # Invalid codes
        assert is_valid_module_code(-1) is False
        assert is_valid_module_code(38) is False
        assert is_valid_module_code(999) is False

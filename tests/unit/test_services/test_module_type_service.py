"""Unit tests for module type service."""

import pytest

from xp.models.telegram.module_type import ModuleType
from xp.services.module_type_service import (
    ModuleTypeNotFoundError,
    ModuleTypeService,
)


class TestModuleTypeService:
    """Test cases for ModuleTypeService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ModuleTypeService()

    def test_get_module_type_by_code(self):
        """Test getting module type by code."""
        module = self.service.get_module_type(14)

        assert isinstance(module, ModuleType)
        assert module.code == 14
        assert module.name == "XP2606"

    def test_get_module_type_by_name(self):
        """Test getting module type by name."""
        module = self.service.get_module_type("XP2606")

        assert isinstance(module, ModuleType)
        assert module.code == 14
        assert module.name == "XP2606"

    def test_get_module_type_by_name_case_insensitive(self):
        """Test getting module type by name is case-insensitive."""
        module = self.service.get_module_type("xp2606")
        assert module.name == "XP2606"

    def test_get_module_type_invalid_code_raises_error(self):
        """Test getting module type with invalid code raises error."""
        with pytest.raises(
            ModuleTypeNotFoundError, match="Module type with code 999 not found"
        ):
            self.service.get_module_type(999)

    def test_get_module_type_invalid_name_raises_error(self):
        """Test getting module type with invalid name raises error."""
        with pytest.raises(
            ModuleTypeNotFoundError, match="Module type with name 'INVALID' not found"
        ):
            self.service.get_module_type("INVALID")

    def test_list_all_modules(self):
        """Test listing all modules."""
        modules = self.service.list_all_modules()

        assert len(modules) == 37
        assert all(isinstance(module, ModuleType) for module in modules)

    def test_list_modules_by_category(self):
        """Test listing modules by category."""
        categories = self.service.list_modules_by_category()

        expected_categories = {
            "Unknown",
            "System",
            "CP Link Modules",
            "XP Control Modules",
            "Interface Panels",
        }
        assert set(categories.keys()) == expected_categories

        # Check total count
        total_modules = sum(len(modules) for modules in categories.values())
        assert total_modules == 37

    def test_search_modules_by_name(self):
        """Test searching modules by name."""
        results = self.service.search_modules("XP2606", search_fields=["name"])

        assert len(results) >= 1
        assert any(module.name == "XP2606" for module in results)

    def test_search_modules_by_description(self):
        """Test searching modules by description."""
        results = self.service.search_modules(
            "push button", search_fields=["description"]
        )

        assert len(results) > 0
        assert all("push button" in module.description.lower() for module in results)

    def test_search_modules_both_fields(self):
        """Test searching modules in both name and description fields."""
        results = self.service.search_modules("XP")

        assert len(results) > 0
        # Should find modules with XP in name or description
        assert any("XP" in module.name for module in results)

    def test_search_modules_case_insensitive(self):
        """Test searching modules is case-insensitive."""
        results1 = self.service.search_modules("xp")
        results2 = self.service.search_modules("XP")

        assert len(results1) == len(results2)
        assert {m.code for m in results1} == {m.code for m in results2}

    def test_search_modules_no_matches(self):
        """Test searching modules with no matches."""
        results = self.service.search_modules("NONEXISTENT")
        assert results == []

    def test_get_modules_by_category_valid(self):
        """Test getting modules by valid category."""
        modules = self.service.get_modules_by_category("System")

        assert len(modules) == 2  # NOMOD and ALLMOD
        assert all(module.category == "System" for module in modules)

    def test_get_modules_by_category_invalid(self):
        """Test getting modules by invalid category."""
        modules = self.service.get_modules_by_category("Invalid Category")
        assert modules == []

    def test_get_push_button_panels(self):
        """Test getting push button panel modules."""
        panels = self.service.get_push_button_panels()

        assert len(panels) > 0
        assert all(panel.is_push_button_panel for panel in panels)

        # Check some specific panels
        panel_names = {panel.name for panel in panels}
        assert "XP2606" in panel_names
        assert "XP2506" in panel_names
        assert "XPX1_8" in panel_names

    def test_get_ir_capable_modules(self):
        """Test getting IR capable modules."""
        ir_modules = self.service.get_ir_capable_modules()

        assert len(ir_modules) > 0
        assert all(module.is_ir_capable for module in ir_modules)

        # Check some specific IR modules
        ir_names = {module.name for module in ir_modules}
        assert "CP70A" in ir_names  # 38kHz IR
        assert "CP70B" in ir_names  # B&O IR

    def test_validate_module_code_valid(self):
        """Test validating valid module codes."""
        assert self.service.validate_module_code(0) is True
        assert self.service.validate_module_code(14) is True
        assert self.service.validate_module_code(23) is True

    def test_validate_module_code_invalid(self):
        """Test validating invalid module codes."""
        assert self.service.validate_module_code(-1) is False
        assert self.service.validate_module_code(38) is False
        assert self.service.validate_module_code(999) is False

    def test_get_module_info_summary_valid_code(self):
        """Test getting module info summary with valid code."""
        summary = self.service.get_module_info_summary(14)

        assert "Module: XP2606 (Code 14)" in summary
        assert "5 way push button panel" in summary
        assert "Category: Interface Panels" in summary
        assert "Push Button Panel" in summary

    def test_get_module_info_summary_valid_name(self):
        """Test getting module info summary with valid name."""
        summary = self.service.get_module_info_summary("XP2606")

        assert "Module: XP2606 (Code 14)" in summary
        assert "5 way push button panel" in summary

    def test_get_module_info_summary_invalid(self):
        """Test getting module info summary with invalid identifier."""
        summary = self.service.get_module_info_summary(999)
        assert "Error:" in summary
        assert "Module type with code 999 not found" in summary

    def test_get_all_modules_summary_simple(self):
        """Test getting all modules summary without grouping."""
        summary = self.service.get_all_modules_summary(group_by_category=False)

        assert "Code | Name       | Description" in summary
        assert "NOMOD" in summary
        assert "XP2606" in summary
        assert "XP134" in summary

    def test_get_all_modules_summary_by_category(self):
        """Test getting all modules summary grouped by category."""
        summary = self.service.get_all_modules_summary(group_by_category=True)

        assert "=== System ===" in summary
        assert "=== CP Link Modules ===" in summary
        assert "=== XP Control Modules ===" in summary
        assert "=== Interface Panels ===" in summary

    def test_format_module_summary_with_features(self):
        """Test formatting module summary includes features."""
        # Test with push button panel + IR capable module
        module = self.service.get_module_type(15)  # XP2606A
        summary = self.service._format_module_summary(module)

        assert "Module: XP2606A (Code 15)" in summary
        assert "Features:" in summary
        assert "Push Button Panel" in summary
        assert "IR Capable" in summary

    def test_format_module_summary_reserved(self):
        """Test formatting module summary for reserved modules."""
        module = self.service.get_module_type(17)  # XP26X1 (Reserved)
        summary = self.service._format_module_summary(module)

        assert "Reserved" in summary

# Copyright (c) 2025 ldvchosal
"""Integration tests for module command functionality."""

import json

from click.testing import CliRunner

from xp.cli.main import cli
from xp.models.telegram.module_type_code import ModuleTypeCode

TOTAL_MODULE_COUNT = 37
SYSTEM_CATEGORY_COUNT = 2  # NOMOD and ALLMOD
UNKNOWN_MODULE_CODE = 99


class TestModuleIntegration:
    """Integration tests for module command functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_module_info_command_by_code(self) -> None:
        """Test that module info command with code works."""
        result = self.runner.invoke(cli, ["module", "info", "14"])

        assert result.exit_code == 0

        # Parse JSON output
        output = json.loads(result.output)
        assert output["code"] == ModuleTypeCode.XP2606.value
        assert output["name"] == "XP2606"
        assert "5 way push button panel" in output["description"]
        assert output["category"] == "Interface Panels"

    def test_module_info_command_by_name(self) -> None:
        """Test module info command with name."""
        result = self.runner.invoke(cli, ["module", "info", "XP2606"])

        assert result.exit_code == 0

        # Parse JSON output
        output = json.loads(result.output)
        assert output["code"] == ModuleTypeCode.XP2606.value
        assert output["name"] == "XP2606"
        assert output["is_push_button_panel"] is True

    def test_module_info_command_json_output(self) -> None:
        """Test module info command with JSON output."""
        result = self.runner.invoke(cli, ["module", "info", "14"])

        assert result.exit_code == 0

        output = json.loads(result.output)
        assert output["code"] == ModuleTypeCode.XP2606.value
        assert output["name"] == "XP2606"
        assert output["category"] == "Interface Panels"
        assert output["is_push_button_panel"] is True

    def test_module_info_command_invalid_code(self) -> None:
        """Test module info command with invalid code."""
        result = self.runner.invoke(cli, ["module", "info", "999"])

        assert result.exit_code == 1

        # Parse JSON error response
        output = json.loads(result.output)
        assert output["success"] is False
        assert "error" in output
        assert "Module type with code 999 not found" in output["error"]

    def test_module_info_command_invalid_code_json(self) -> None:
        """Test module info command with invalid code and JSON output."""
        result = self.runner.invoke(cli, ["module", "info", "999"])

        assert result.exit_code == 1

        output = json.loads(result.output)
        assert output["success"] is False
        assert "error" in output
        assert "999" in output["error"]

    def test_module_list_command(self) -> None:
        """Test module list command."""
        result = self.runner.invoke(cli, ["module", "list"])

        assert result.exit_code == 0

        # Parse JSON output
        output = json.loads(result.output)
        assert "modules" in output
        assert "count" in output
        # Check for specific modules
        module_names = [m["name"] for m in output["modules"]]
        assert "NOMOD" in module_names
        assert "XP2606" in module_names

    def test_module_list_command_json_output(self) -> None:
        """Test module list command with JSON output."""
        result = self.runner.invoke(cli, ["module", "list"])

        assert result.exit_code == 0

        output = json.loads(result.output)
        assert "modules" in output
        assert "count" in output
        assert output["count"] == TOTAL_MODULE_COUNT
        assert len(output["modules"]) == TOTAL_MODULE_COUNT

    def test_module_list_command_by_category(self) -> None:
        """Test module list command filtered by category."""
        result = self.runner.invoke(cli, ["module", "list", "--category", "System"])

        assert result.exit_code == 0

        # Parse JSON output
        output = json.loads(result.output)
        assert "modules" in output
        # Check for specific modules in System category
        module_names = [m["name"] for m in output["modules"]]
        assert "NOMOD" in module_names
        assert "ALLMOD" in module_names

    def test_module_list_command_group_by_category(self) -> None:
        """Test module list command grouped by category."""
        result = self.runner.invoke(cli, ["module", "list", "--group-by-category"])

        assert result.exit_code == 0

        # Parse JSON output
        output = json.loads(result.output)
        assert "modules_by_category" in output
        assert "System" in output["modules_by_category"]
        assert "CP Link Modules" in output["modules_by_category"]
        assert "XP Control Modules" in output["modules_by_category"]
        assert "Interface Panels" in output["modules_by_category"]

    def test_module_list_command_group_by_category_json(self) -> None:
        """Test module list command grouped by category with JSON output."""
        result = self.runner.invoke(cli, ["module", "list", "--group-by-category"])

        assert result.exit_code == 0

        output = json.loads(result.output)
        assert "modules_by_category" in output
        assert "System" in output["modules_by_category"]
        assert "Interface Panels" in output["modules_by_category"]

    def test_module_list_command_invalid_category(self) -> None:
        """Test module list command with invalid category."""
        result = self.runner.invoke(cli, ["module", "list", "--category", "Invalid"])

        assert result.exit_code == 0

        # Parse JSON output
        output = json.loads(result.output)
        assert "modules" in output
        assert len(output["modules"]) == 0
        assert output["category"] == "Invalid"

    def test_module_search_command(self) -> None:
        """Test module search command."""
        result = self.runner.invoke(cli, ["module", "search", "push button"])

        assert result.exit_code == 0

        # Parse JSON output
        output = json.loads(result.output)
        assert output["query"] == "push button"
        assert output["count"] >= 1
        assert "matches" in output
        # Check that XP2606 is in the search results
        match_names = [m["name"] for m in output["matches"]]
        assert "XP2606" in match_names

    def test_module_search_command_json_output(self) -> None:
        """Test module search command with JSON output."""
        result = self.runner.invoke(cli, ["module", "search", "XP2606"])

        assert result.exit_code == 0

        output = json.loads(result.output)
        assert output["query"] == "XP2606"
        assert output["count"] >= 1
        assert "matches" in output
        assert any(match["name"] == "XP2606" for match in output["matches"])

    def test_module_search_command_by_name_field(self) -> None:
        """Test module search command searching only name field."""
        result = self.runner.invoke(cli, ["module", "search", "XP", "--field", "name"])

        assert result.exit_code == 0
        assert "XP2606" in result.output
        assert "XP24" in result.output

    def test_module_search_command_no_matches(self) -> None:
        """Test module search command with no matches."""
        result = self.runner.invoke(cli, ["module", "search", "NONEXISTENT"])

        assert result.exit_code == 0

        # Parse JSON output
        output = json.loads(result.output)
        assert output["query"] == "NONEXISTENT"
        assert output["count"] == 0
        assert len(output["matches"]) == 0

    def test_module_categories_command(self) -> None:
        """Test module categories command."""
        result = self.runner.invoke(cli, ["module", "categories"])

        assert result.exit_code == 0

        # Parse JSON output
        output = json.loads(result.output)
        assert "categories" in output
        assert "System" in output["categories"]
        assert "Interface Panels" in output["categories"]

    def test_module_categories_command_json_output(self) -> None:
        """Test module categories command with JSON output."""
        result = self.runner.invoke(cli, ["module", "categories"])

        assert result.exit_code == 0

        output = json.loads(result.output)
        assert "categories" in output
        assert "System" in output["categories"]
        assert "Interface Panels" in output["categories"]
        assert output["categories"]["System"] == SYSTEM_CATEGORY_COUNT

    def test_module_help_command(self) -> None:
        """Test module help command."""
        result = self.runner.invoke(cli, ["module", "--help"])

        assert result.exit_code == 0
        assert "module type operations" in result.output
        assert "info" in result.output
        assert "list" in result.output
        assert "search" in result.output
        assert "categories" in result.output

    def test_module_subcommand_help(self) -> None:
        """Test module subcommand help."""
        result = self.runner.invoke(cli, ["module", "info", "--help"])

        assert result.exit_code == 0
        assert "Get information about a module type" in result.output
        assert "Examples:" in result.output
        assert "xp module info 14" in result.output

    def test_enhanced_telegram_parsing_with_module_info(self) -> None:
        """Test that telegram parsing now includes module information."""
        result = self.runner.invoke(cli, ["telegram", "parse", "<E14L00I02MAK>"])

        assert result.exit_code == 0

        output = json.loads(result.output)
        assert output["module_type"] == ModuleTypeCode.XP2606.value
        assert "module_info" in output
        assert output["module_info"]["name"] == "XP2606"
        assert (
            output["module_info"]["description"]
            == "5 way push button panel with sesam, L-Team design"
        )
        assert output["module_info"]["category"] == "Interface Panels"

    def test_enhanced_telegram_parsing_human_readable(self) -> None:
        """Test that telegram parsing includes module names in JSON."""
        result = self.runner.invoke(cli, ["telegram", "parse", "<E14L00I02MAK>"])

        assert result.exit_code == 0

        # Parse JSON output
        output = json.loads(result.output)
        assert output["module_type"] == ModuleTypeCode.XP2606.value
        assert "module_info" in output
        assert output["module_info"]["name"] == "XP2606"
        assert output["event_type_name"] == "button_press"

    def test_enhanced_telegram_parsing_unknown_module(self) -> None:
        """Test telegram parsing with unknown module type."""
        # Test with a module type that doesn't exist (using high number)
        # This tests the graceful handling when module_info is None
        result = self.runner.invoke(cli, ["telegram", "parse", "<E99L00I02MAK>"])

        assert result.exit_code == 0

        output = json.loads(result.output)
        assert output["module_type"] == UNKNOWN_MODULE_CODE
        assert output["module_info"] is None

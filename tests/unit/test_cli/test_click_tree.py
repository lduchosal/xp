# Copyright (c) 2025 ldvchosal
"""Tests for click_tree utility."""

import click
from click.testing import CliRunner

from xp.cli.utils.click_tree import add_tree_command


class TestAddTreeCommand:
    """Test add_tree_command function."""

    def test_add_tree_command_to_group(self) -> None:
        """Test adding tree command to a Click group."""

        @click.group()
        def cli() -> None:
            """Test CLI."""

        @cli.command()
        def subcommand() -> None:
            """Provide a test subcommand."""

        tree_cmd = add_tree_command(cli, "tree")
        assert tree_cmd is not None
        assert tree_cmd.name == "tree"

    def test_tree_command_execution_simple_group(self) -> None:
        """Test tree command execution with simple group."""

        @click.group()
        def cli() -> None:
            """Test CLI."""

        @cli.command()
        def cmd1() -> None:
            """First command."""

        @cli.command()
        def cmd2() -> None:
            """Second command."""

        add_tree_command(cli, "tree")

        result = CliRunner().invoke(cli, ["tree"])
        assert result.exit_code == 0
        assert "cli" in result.output
        assert "cmd1" in result.output
        assert "cmd2" in result.output

    def test_tree_command_execution_nested_groups(self) -> None:
        """Test tree command with nested groups."""

        @click.group()
        def cli() -> None:
            """Provide main CLI."""

        @cli.group()
        def group1() -> None:
            """First group."""

        @group1.command("nested")
        def nested_cmd() -> None:
            """Nested command."""

        @cli.command("top-level")
        def top_level_cmd() -> None:
            """Top level command."""

        add_tree_command(cli, "tree")

        result = CliRunner().invoke(cli, ["tree"])
        assert result.exit_code == 0
        assert "cli" in result.output
        assert "group1" in result.output
        assert "nested" in result.output
        assert "top-level" in result.output

    def test_tree_command_default_name(self) -> None:
        """Test tree command with default name."""

        @click.group()
        def cli() -> None:
            """Test CLI."""

        tree_cmd = add_tree_command(cli)
        assert tree_cmd.name == "help"

    def test_tree_command_custom_name(self) -> None:
        """Test tree command with custom name."""

        @click.group()
        def cli() -> None:
            """Test CLI."""

        tree_cmd = add_tree_command(cli, "mytree")
        assert tree_cmd.name == "mytree"

    def test_tree_command_with_short_help(self) -> None:
        """Test tree command displays short help."""

        @click.group(short_help="Short description")
        def cli() -> None:
            """Test CLI."""

        add_tree_command(cli, "tree")

        result = CliRunner().invoke(cli, ["tree"])
        assert result.exit_code == 0
        assert "Short description" in result.output

    def test_tree_command_empty_group(self) -> None:
        """Test tree command with empty group."""

        @click.group()
        def cli() -> None:
            """Empty CLI."""

        add_tree_command(cli, "tree")

        result = CliRunner().invoke(cli, ["tree"])
        assert result.exit_code == 0
        assert "cli" in result.output

    def test_tree_command_deeply_nested_groups(self) -> None:
        """Test tree command with deeply nested groups."""

        @click.group()
        def cli() -> None:
            """Provide main CLI."""

        @cli.group()
        def level1() -> None:
            """Level 1 group."""

        @level1.group()
        def level2() -> None:
            """Level 2 group."""

        @level2.command("deep")
        def deep_cmd() -> None:
            """Deep command."""

        add_tree_command(cli, "tree")

        result = CliRunner().invoke(cli, ["tree"])
        assert result.exit_code == 0
        assert "cli" in result.output
        assert "level1" in result.output
        assert "level2" in result.output
        assert "deep" in result.output

    def test_tree_command_multiple_nested_groups(self) -> None:
        """Test tree command with multiple nested groups at same level."""

        @click.group()
        def cli() -> None:
            """Provide main CLI."""

        @cli.group()
        def group1() -> None:
            """First group."""

        @cli.group()
        def group2() -> None:
            """Second group."""

        @group1.command()
        def cmd1() -> None:
            """Command 1."""

        @group2.command()
        def cmd2() -> None:
            """Command 2."""

        add_tree_command(cli, "tree")

        result = CliRunner().invoke(cli, ["tree"])
        assert result.exit_code == 0
        assert "group1" in result.output
        assert "group2" in result.output
        assert "cmd1" in result.output
        assert "cmd2" in result.output

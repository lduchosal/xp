"""Tests for click_tree utility."""

import click
from click.testing import CliRunner

from xp.cli.utils.click_tree import add_tree_command


class TestAddTreeCommand:
    """Test add_tree_command function."""

    def test_add_tree_command_to_group(self):
        """Test adding tree command to a Click group."""

        @click.group()
        def cli():
            """Test CLI."""
            pass

        @cli.command()
        def subcommand():
            """Provide a test subcommand."""
            pass

        tree_cmd = add_tree_command(cli, "tree")
        assert tree_cmd is not None
        assert tree_cmd.name == "tree"

    def test_tree_command_execution_simple_group(self):
        """Test tree command execution with simple group."""

        @click.group()
        def cli():
            """Test CLI."""
            pass

        @cli.command()
        def cmd1():
            """First command."""
            pass

        @cli.command()
        def cmd2():
            """Second command."""
            pass

        add_tree_command(cli, "tree")

        result = CliRunner().invoke(cli, ["tree"])
        assert result.exit_code == 0
        assert "cli" in result.output
        assert "cmd1" in result.output
        assert "cmd2" in result.output

    def test_tree_command_execution_nested_groups(self):
        """Test tree command with nested groups."""

        @click.group()
        def cli():
            """Provide main CLI."""
            pass

        @cli.group()
        def group1():
            """First group."""
            pass

        @group1.command("nested")
        def nested_cmd():
            """Nested command."""
            pass

        @cli.command("top-level")
        def top_level_cmd():
            """Top level command."""
            pass

        add_tree_command(cli, "tree")

        result = CliRunner().invoke(cli, ["tree"])
        assert result.exit_code == 0
        assert "cli" in result.output
        assert "group1" in result.output
        assert "nested" in result.output
        assert "top-level" in result.output

    def test_tree_command_default_name(self):
        """Test tree command with default name."""

        @click.group()
        def cli():
            """Test CLI."""
            pass

        tree_cmd = add_tree_command(cli)
        assert tree_cmd.name == "help"

    def test_tree_command_custom_name(self):
        """Test tree command with custom name."""

        @click.group()
        def cli():
            """Test CLI."""
            pass

        tree_cmd = add_tree_command(cli, "mytree")
        assert tree_cmd.name == "mytree"

    def test_tree_command_with_short_help(self):
        """Test tree command displays short help."""

        @click.group(short_help="Short description")
        def cli():
            """Test CLI."""
            pass

        add_tree_command(cli, "tree")

        result = CliRunner().invoke(cli, ["tree"])
        assert result.exit_code == 0
        assert "Short description" in result.output

    def test_tree_command_empty_group(self):
        """Test tree command with empty group."""

        @click.group()
        def cli():
            """Empty CLI."""
            pass

        add_tree_command(cli, "tree")

        result = CliRunner().invoke(cli, ["tree"])
        assert result.exit_code == 0
        assert "cli" in result.output

    def test_tree_command_deeply_nested_groups(self):
        """Test tree command with deeply nested groups."""

        @click.group()
        def cli():
            """Provide main CLI."""
            pass

        @cli.group()
        def level1():
            """Level 1 group."""
            pass

        @level1.group()
        def level2():
            """Level 2 group."""
            pass

        @level2.command("deep")
        def deep_cmd():
            """Deep command."""
            pass

        add_tree_command(cli, "tree")

        result = CliRunner().invoke(cli, ["tree"])
        assert result.exit_code == 0
        assert "cli" in result.output
        assert "level1" in result.output
        assert "level2" in result.output
        assert "deep" in result.output

    def test_tree_command_multiple_nested_groups(self):
        """Test tree command with multiple nested groups at same level."""

        @click.group()
        def cli():
            """Provide main CLI."""
            pass

        @cli.group()
        def group1():
            """First group."""
            pass

        @cli.group()
        def group2():
            """Second group."""
            pass

        @group1.command()
        def cmd1():
            """Command 1."""
            pass

        @group2.command()
        def cmd2():
            """Command 2."""
            pass

        add_tree_command(cli, "tree")

        result = CliRunner().invoke(cli, ["tree"])
        assert result.exit_code == 0
        assert "group1" in result.output
        assert "group2" in result.output
        assert "cmd1" in result.output
        assert "cmd2" in result.output

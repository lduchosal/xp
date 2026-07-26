# Copyright (c) 2025 ldvchosal
"""Utilities for displaying Click command trees."""

import click


def add_tree_command(
    cli_group: click.Group, command_name: str = "help"
) -> click.Command:
    """Add a tree command to any Click group.

    Args:
        cli_group: The Click group to add the tree command to.
        command_name: Name of the tree command (default: "help").

    Returns:
        The tree command function.

    """

    def print_command_tree(group: click.Group, ctx: click.Context, suffix: str) -> None:
        """Print command tree recursively.

        Args:
            group: The Click group to print.
            ctx: The Click context.
            suffix: Prefix string for tree display.

        """
        for name in sorted(group.list_commands(ctx)):
            cmd = group.get_command(ctx, name)

            if isinstance(cmd, click.Group):
                click.echo()
                click.echo(f"{suffix} {name}")
                print_command_tree(cmd, ctx, f"{suffix} {name}")
                click.echo()
            else:
                click.echo(f"{suffix} {name}")

    @cli_group.command(command_name)
    @click.pass_context
    def tree_command(ctx: click.Context) -> None:
        """Show complete command tree.

        Args:
            ctx: The Click context.

        """
        root = ctx.find_root().command
        root_ctx = ctx.find_root()
        root_name = root_ctx.info_name or "cli"
        click.echo()
        click.echo(root_name)
        if root.short_help:
            click.echo(str(root.short_help))
        if isinstance(root, click.Group):
            print_command_tree(root, root_ctx, root_name)

    return tree_command

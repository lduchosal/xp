# save as click_tree.py
import click
from typing import Any


def add_tree_command(cli_group: click.Group, command_name: str = "help") -> Any:
    """Add a tree command to any Click group"""

    def print_command_tree(group: click.Group, ctx: click.Context, suffix: str) -> None:
        for name in sorted(group.list_commands(ctx)):
            cmd = group.get_command(ctx, name)

            if isinstance(cmd, click.Group):
                # print(f"")
                print()
                print(f"{suffix} {name}")
                print_command_tree(cmd, ctx, f"{suffix} {name}")
                print()
            else:
                print(f"{suffix} {name}")

    @cli_group.command(command_name)
    @click.pass_context
    def tree_command(ctx: click.Context) -> None:
        """Show complete command tree"""
        root = ctx.find_root().command
        root_ctx = ctx.find_root()
        root_name = root_ctx.info_name or "cli"
        print()
        print(root_name)
        if root.short_help:
            print(str(root.short_help))
        if isinstance(root, click.Group):
            print_command_tree(root, root_ctx, root_name)

    return tree_command

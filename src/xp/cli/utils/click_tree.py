# save as click_tree.py
import click

def add_tree_command(cli_group, command_name='help'):
    """Add a tree command to any Click group"""

    def print_command_tree(group, ctx, suffix):
        for name in sorted(group.list_commands(ctx)):
            cmd = group.get_command(ctx, name)

            if isinstance(cmd, click.Group):
                # print(f"")
                print("")
                print(f"{suffix} {name}")
                print_command_tree(cmd, ctx, f"{suffix} {name}")
                print("")
            else:
                print(f"{suffix} {name}")

    @cli_group.command(command_name)
    @click.pass_context
    def tree_command(ctx):
        """Show complete command tree"""
        root = ctx.find_root().command
        print("")
        print(f"{ctx.find_root().info_name}")
        if root.short_help:
            print(f"{root.short_help}")
        print_command_tree(root, ctx.find_root(), ctx.find_root().info_name)

    return tree_command


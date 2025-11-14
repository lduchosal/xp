"""XP CLI tool entry point with modular command structure."""

import click
from click_help_colors import HelpColorsGroup

from xp.cli.commands import homekit
from xp.cli.commands.conbus.conbus import conbus
from xp.cli.commands.file_commands import file
from xp.cli.commands.module_commands import module

# Import all conbus command modules to register their commands
from xp.cli.commands.reverse_proxy_commands import reverse_proxy
from xp.cli.commands.server.server_commands import server

# Import command groups from modular structure
from xp.cli.commands.telegram.telegram_parse_commands import telegram
from xp.cli.commands.term.term import term
from xp.cli.utils.click_tree import add_tree_command
from xp.utils.dependencies import ServiceContainer
from xp.utils.logging import LoggerService


@click.group(
    cls=HelpColorsGroup, help_headers_color="yellow", help_options_color="green"
)
@click.version_option()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """XP CLI tool for remote console bus operations.

    Args:
        ctx: Click context object for passing state between commands.
    """
    container = ServiceContainer()
    logger_config = container.get_container().resolve(LoggerService)
    logger_config.setup()

    # Initialize the service container and store it in the context
    ctx.ensure_object(dict)
    # Only create a new container if one wasn't provided (e.g., for testing)
    if "container" not in ctx.obj:
        ctx.obj["container"] = container


# Register all command groups
cli.add_command(conbus)
cli.add_command(homekit)
cli.add_command(telegram)
cli.add_command(module)
cli.add_command(file)
cli.add_command(server)
cli.add_command(reverse_proxy)
cli.add_command(term)

# Add the tree command
add_tree_command(cli)

if __name__ == "__main__":
    cli()

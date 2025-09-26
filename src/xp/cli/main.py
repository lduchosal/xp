"""XP CLI tool entry point with modular command structure."""

import logging

import click
from click_help_colors import HelpColorsGroup

from xp.cli.commands import homekit
from xp.cli.utils.click_tree import add_tree_command
from .commands.api import api
from .commands.cache_commands import cache
from .commands.conbus import conbus
from .commands.file_commands import file
from .commands.module_commands import module

# Import all conbus command modules to register their commands
from .commands.reverse_proxy_commands import reverse_proxy
from .commands.server_commands import server

# Import command groups from modular structure
from .commands.telegram_parse_commands import telegram


@click.group(
    cls=HelpColorsGroup, help_headers_color="yellow", help_options_color="green"
)
@click.version_option()
def cli() -> None:
    """XP CLI tool for remote console bus operations"""
    logging.basicConfig(level=logging.DEBUG)
    # Suppress pyhap.hap_protocol logs
    logging.getLogger("pyhap.hap_protocol").setLevel(logging.WARNING)
    logging.getLogger("pyhap.hap_handler").setLevel(logging.WARNING)
    # logging.getLogger('pyhap.accessory_driver').setLevel(logging.WARNING)

    pass


# Register all command groups
cli.add_command(cache)
cli.add_command(conbus)
cli.add_command(homekit)
cli.add_command(telegram)
cli.add_command(module)
cli.add_command(file)
cli.add_command(server)
cli.add_command(api)
cli.add_command(reverse_proxy)

# Add the tree command
add_tree_command(cli)

if __name__ == "__main__":
    cli()

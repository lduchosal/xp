"""XP CLI tool entry point with modular command structure."""

import click
from click_help_colors import HelpColorsGroup, HelpColorsCommand

# Import command groups from modular structure
from .commands.telegram_commands import telegram
from .commands.module_commands import module
from .commands.checksum_commands import checksum
from .commands.file_commands import file
from .commands.server_commands import server
from .commands.conbus import conbus

# Import all conbus command modules to register their commands
from .commands.reverse_proxy_commands import reverse_proxy


@click.group(cls=HelpColorsGroup, help_headers_color='yellow', help_options_color='green')
@click.version_option()
def cli():
    """XP CLI tool for remote console bus operations"""
    pass


# Register all command groups
cli.add_command(telegram)
cli.add_command(module)
cli.add_command(checksum)
cli.add_command(file)
cli.add_command(server)
cli.add_command(conbus)
cli.add_command(reverse_proxy)

if __name__ == "__main__":
    cli()

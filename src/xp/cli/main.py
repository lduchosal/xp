"""XP CLI tool entry point with modular command structure."""
import click

# Import command groups from modular structure
from .commands.telegram_commands import telegram
from .commands.module_commands import module
from .commands.checksum_commands import checksum
from .commands.linknumber_commands import linknumber
from .commands.version_commands import version
from .commands.discovery_commands import discovery
from .commands.file_commands import file
from .commands.server_commands import server
from .commands.conbus_commands import conbus
from .commands.reverse_proxy_commands import reverse_proxy


@click.group()
@click.version_option()
def cli():
    """XP CLI tool for remote console bus operations"""
    pass


# Register all command groups
cli.add_command(telegram)
cli.add_command(module)
cli.add_command(checksum)
cli.add_command(linknumber)
cli.add_command(version)
cli.add_command(discovery)
cli.add_command(file)
cli.add_command(server)
cli.add_command(conbus)
cli.add_command(reverse_proxy)


if __name__ == '__main__':
    cli()
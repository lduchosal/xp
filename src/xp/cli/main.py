"""XP CLI tool entry point with modular command structure."""

import click

# Import command groups from modular structure
from .commands.telegram_commands import telegram
from .commands.module_commands import module
from .commands.checksum_commands import checksum
from .commands.telegram_linknumber_commands import linknumber
from .commands.telegram_blink_commands import blink
from .commands.telegram_discovery_commands import discovery
from .commands.file_commands import file
from .commands.server_commands import server
from .commands.conbus import conbus
# Import all conbus command modules to register their commands
from .commands import conbus_send_commands
from .commands import conbus_config_commands
from .commands import conbus_scan_commands
from .commands import conbus_input_commands
from .commands import conbus_custom_commands
from .commands import conbus_blink_commands
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
cli.add_command(blink)
cli.add_command(discovery)
cli.add_command(file)
cli.add_command(server)
cli.add_command(conbus)
cli.add_command(reverse_proxy)


# Register legacy blink commands as top-level commands (for compatibility with spec)
@cli.command("blink")
@click.argument("serial_number")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
def blink_legacy(serial_number: str, json_output: bool):
    """Start blinking module LED (legacy command)"""
    from .commands.telegram_blink_commands import blink_on

    blink_on.callback(serial_number, json_output)


@cli.command("unblink")
@click.argument("serial_number")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
def unblink_legacy(serial_number: str, json_output: bool):
    """Stop blinking module LED (legacy command)"""
    from .commands.telegram_blink_commands import blink_off

    blink_off.callback(serial_number, json_output)


if __name__ == "__main__":
    cli()

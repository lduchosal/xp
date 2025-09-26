"""Shared conbus CLI group definition."""

import click
from click_help_colors import HelpColorsGroup

from .conbus_datapoint_commands import conbus_datapoint_group

@click.group(cls=HelpColorsGroup, help_headers_color='yellow', help_options_color='green')
def conbus() -> None:
    """
    Conbus client operations for sending telegrams to remote servers
    """
    pass

@click.group(name="blink", cls=HelpColorsGroup, help_headers_color='yellow', help_options_color='green')
def conbus_blink() -> None:
    """
    Conbus client operations for sending blink telegrams to remote servers
    """
    pass


@click.group(name="output", cls=HelpColorsGroup, help_headers_color='yellow', help_options_color='green')
def conbus_output() -> None:
    """
    Conbus input operations to remote servers
    """
    pass

conbus.add_command(conbus_blink)
conbus.add_command(conbus_output)
conbus.add_command(conbus_datapoint_group)  # type: ignore[has-type]

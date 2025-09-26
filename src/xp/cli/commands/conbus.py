"""Shared conbus CLI group definition."""

import click
from click_help_colors import HelpColorsGroup

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


@click.group(name="datapoint", cls=HelpColorsGroup, help_headers_color='yellow', help_options_color='green')
def conbus_datapoint() -> None:
    """
    Conbus datapoint operations for querying module datapoints
    """
    pass

@click.group("linknumber", cls=HelpColorsGroup, help_headers_color='yellow', help_options_color='green', short_help="Link number operations")
def conbus_linknumber() -> None:
    """
    Link number operations for modules.

    Set or get the link number for specific modules.
    """
    pass

conbus.add_command(conbus_blink)
conbus.add_command(conbus_output)
conbus.add_command(conbus_datapoint)
conbus.add_command(conbus_linknumber)

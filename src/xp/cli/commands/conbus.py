"""Shared conbus CLI group definition."""

import click
from click_help_colors import HelpColorsGroup


@click.group(
    cls=HelpColorsGroup, help_headers_color="yellow", help_options_color="green"
)
def conbus() -> None:
    """
    Conbus client operations for sending telegrams to remote servers
    """
    pass


@click.group(
    name="blink",
    cls=HelpColorsGroup,
    help_headers_color="yellow",
    help_options_color="green",
)
def conbus_blink() -> None:
    """
    Conbus client operations for sending blink telegrams to remote servers
    """
    pass


@click.group(
    name="output",
    cls=HelpColorsGroup,
    help_headers_color="yellow",
    help_options_color="green",
)
def conbus_output() -> None:
    """
    Conbus input operations to remote servers
    """
    pass


@click.group(
    name="datapoint",
    cls=HelpColorsGroup,
    help_headers_color="yellow",
    help_options_color="green",
)
def conbus_datapoint() -> None:
    """
    Conbus datapoint operations for querying module datapoints
    """
    pass


@click.group(
    "linknumber",
    cls=HelpColorsGroup,
    help_headers_color="yellow",
    help_options_color="green",
    short_help="Link number operations",
)
def conbus_linknumber() -> None:
    """
    Link number operations for modules.

    Set or get the link number for specific modules.
    """
    pass


@click.group(
    "autoreport",
    cls=HelpColorsGroup,
    help_headers_color="yellow",
    help_options_color="green",
    short_help="Auto report status operations",
)
def conbus_autoreport() -> None:
    """
    Auto report status operations for modules.

    Get or set the auto report status for specific modules.
    """
    pass


@click.group(
    "lightlevel",
    cls=HelpColorsGroup,
    help_headers_color="yellow",
    help_options_color="green",
    short_help="Light level operations",
)
def conbus_lightlevel() -> None:
    """
    Light level operations for modules.

    Control light level (dimming) of outputs on Conbus modules.
    """
    pass


@click.group(
    "msactiontable",
    cls=HelpColorsGroup,
    help_headers_color="yellow",
    help_options_color="green",
    short_help="MSActionTable operations",
)
def conbus_msactiontable() -> None:
    """
    msactiontable operations for modules.

    Download msactiontable on Conbus modules.
    """
    pass


@click.group(
    "actiontable",
    cls=HelpColorsGroup,
    help_headers_color="yellow",
    help_options_color="green",
    short_help="ActionTable operations",
)
def conbus_actiontable() -> None:
    """
    ActionTable operations for modules.

    Download ActionTable from Conbus modules.
    """
    pass


conbus.add_command(conbus_blink)
conbus.add_command(conbus_output)
conbus.add_command(conbus_datapoint)
conbus.add_command(conbus_linknumber)
conbus.add_command(conbus_autoreport)
conbus.add_command(conbus_lightlevel)
conbus.add_command(conbus_msactiontable)
conbus.add_command(conbus_actiontable)

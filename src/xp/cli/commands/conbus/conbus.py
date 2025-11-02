"""Shared conbus CLI group definition."""

import click
from click_help_colors import HelpColorsGroup


@click.group(
    cls=HelpColorsGroup, help_headers_color="yellow", help_options_color="green"
)
def conbus() -> None:
    """Perform Conbus client operations for sending telegrams to remote servers."""
    pass


@click.group(
    name="blink",
    cls=HelpColorsGroup,
    help_headers_color="yellow",
    help_options_color="green",
)
def conbus_blink() -> None:
    """Perform Conbus client operations for sending blink telegrams to remote servers."""
    pass


@click.group(
    name="output",
    cls=HelpColorsGroup,
    help_headers_color="yellow",
    help_options_color="green",
)
def conbus_output() -> None:
    """Perform Conbus input operations to remote servers."""
    pass


@click.group(
    name="datapoint",
    cls=HelpColorsGroup,
    help_headers_color="yellow",
    help_options_color="green",
)
def conbus_datapoint() -> None:
    """Perform Conbus datapoint operations for querying module datapoints."""
    pass


@click.group(
    "linknumber",
    cls=HelpColorsGroup,
    help_headers_color="yellow",
    help_options_color="green",
    short_help="Link number operations",
)
def conbus_linknumber() -> None:
    """Set or get the link number for specific modules."""
    pass


@click.group(
    "modulenumber",
    cls=HelpColorsGroup,
    help_headers_color="yellow",
    help_options_color="green",
    short_help="Module number operations",
)
def conbus_modulenumber() -> None:
    """Set or get the module number for specific modules."""
    pass


@click.group(
    "autoreport",
    cls=HelpColorsGroup,
    help_headers_color="yellow",
    help_options_color="green",
    short_help="Auto report status operations",
)
def conbus_autoreport() -> None:
    """Get or set the auto report status for specific modules."""
    pass


@click.group(
    "lightlevel",
    cls=HelpColorsGroup,
    help_headers_color="yellow",
    help_options_color="green",
    short_help="Light level operations",
)
def conbus_lightlevel() -> None:
    """Control light level (dimming) of outputs on Conbus modules."""
    pass


@click.group(
    "msactiontable",
    cls=HelpColorsGroup,
    help_headers_color="yellow",
    help_options_color="green",
    short_help="MSActionTable operations",
)
def conbus_msactiontable() -> None:
    """Download msactiontable on Conbus modules."""
    pass


@click.group(
    "actiontable",
    cls=HelpColorsGroup,
    help_headers_color="yellow",
    help_options_color="green",
    short_help="ActionTable operations",
)
def conbus_actiontable() -> None:
    """Download ActionTable from Conbus modules."""
    pass


conbus.add_command(conbus_blink)
conbus.add_command(conbus_output)
conbus.add_command(conbus_datapoint)
conbus.add_command(conbus_linknumber)
conbus.add_command(conbus_modulenumber)
conbus.add_command(conbus_autoreport)
conbus.add_command(conbus_lightlevel)
conbus.add_command(conbus_msactiontable)
conbus.add_command(conbus_actiontable)

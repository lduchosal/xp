"""Shared conbus CLI group definition."""

import click
from click_help_colors import HelpColorsGroup


@click.group(
    cls=HelpColorsGroup, help_headers_color="yellow", help_options_color="green"
)
def telegram() -> None:
    """Perform event telegram operations."""
    pass


@click.group(
    cls=HelpColorsGroup, help_headers_color="yellow", help_options_color="green"
)
def linknumber() -> None:
    """Perform link number operations for module configuration."""
    pass


@click.group(
    cls=HelpColorsGroup, help_headers_color="yellow", help_options_color="green"
)
def blink() -> None:
    """Perform blink operations for module LED control."""
    pass


@click.group(
    cls=HelpColorsGroup, help_headers_color="yellow", help_options_color="green"
)
def checksum() -> None:
    """Perform checksum calculation and validation operations."""
    pass


telegram.add_command(linknumber)
telegram.add_command(blink)
telegram.add_command(checksum)

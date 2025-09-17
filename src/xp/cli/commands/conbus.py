"""Shared conbus CLI group definition."""

import click
from click_help_colors import HelpColorsGroup

@click.group(cls=HelpColorsGroup, help_headers_color='yellow', help_options_color='green')
def conbus():
    """
    Conbus client operations for sending telegrams to remote servers
    """
    pass

@click.group(cls=HelpColorsGroup, help_headers_color='yellow', help_options_color='green')
def blink():
    """
    Conbus client operations for sending blink telegrams to remote servers
    """
    pass

conbus.add_command(blink)

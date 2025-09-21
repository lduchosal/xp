"""API server management CLI commands."""

import click
from click_help_colors import HelpColorsGroup

@click.group(cls=HelpColorsGroup, help_headers_color='yellow', help_options_color='green')
def homekit():
    """
    API server management commands.

    Manage the HomeKit server for XP Protocol operations.
    """
    pass

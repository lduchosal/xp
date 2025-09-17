"""API server management CLI commands."""

import click


@click.group()
def api():
    """
    API server management commands.

    Manage the FastAPI server for XP Protocol operations.
    """
    pass
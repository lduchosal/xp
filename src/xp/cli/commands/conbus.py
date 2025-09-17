"""Shared conbus CLI group definition."""

import click


@click.group()
def conbus():
    """
    Conbus client operations for sending telegrams to remote servers
    """
    pass
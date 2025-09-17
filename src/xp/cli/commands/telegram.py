"""Shared conbus CLI group definition."""

import click

@click.group()
def telegram():
    """
    Event telegram operations
    """
    pass

@click.group()
def linknumber():
    """
    Link number operations for module configuration
    """
    pass

@click.group()
def blink():
    """
    Blink operations for module LED control
    """
    pass

@click.group()
def discovery():
    """
    Device discovery operations for console bus enumeration
    """
    pass


telegram.add_command(linknumber)
telegram.add_command(blink)
telegram.add_command(discovery)

"""Conbus raw telegram CLI commands."""

import click

from .conbus import conbus
from ..utils.decorators import (
    connection_command,
    handle_service_errors,
)
from ..utils.error_handlers import CLIErrorHandler
from ...services.conbus_raw_service import ConbusRawService, ConbusRawError


@conbus.command("raw")
@click.argument("raw_telegrams")
@connection_command()
@handle_service_errors(ConbusRawError)
def send_raw_telegrams(raw_telegrams: str):
    """
    Send raw telegram sequence to Conbus server.

    Accepts a string containing one or more telegrams in format <...>.
    Multiple telegrams should be concatenated without separators.

    Examples:

    \b
        xp conbus raw '<S2113010000F02D12>'
        xp conbus raw '<S2113010000F02D12><S2113010001F02D12><S2113010002F02D12>'
        xp conbus raw '<S0020042796F02D12FM><S0020044991F02D12FD><S0020044974F02D12FI><S0020044966F02D12FL><S0020044989F02D12FK><S0020044964F02D12FJ><S0020044986F02D12FF>'
    """
    service = ConbusRawService()

    try:
        with service:
            response = service.send_raw_telegrams(raw_telegrams)

        # Format output to match expected format from documentation
        if response.success and response.received_telegrams:
            for telegram in response.received_telegrams:
                click.echo(telegram)
        elif response.success:
            click.echo("No response received")
        else:
            click.echo(f"Error: {response.error}", err=True)

    except ConbusRawError as e:
        CLIErrorHandler.handle_service_error(e, "raw telegram send", {
            "raw_telegrams": raw_telegrams,
        })
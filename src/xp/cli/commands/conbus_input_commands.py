"""Conbus client operations CLI commands."""

import click
import json

from ..utils.serial_number_type import SERIAL
from ...models.action_type import ActionType
from ...services.conbus_datapoint_service import (
    ConbusDatapointError,
)
from ...services.conbus_input_service import ConbusInputService
from ..utils.decorators import (
    connection_command,
    handle_service_errors,
)
from .conbus import conbus_input

@conbus_input.command("on")
@click.argument("serial_number", type=SERIAL)
@click.argument("input_number", type=int)
@connection_command()
@handle_service_errors(ConbusDatapointError)
def xp_input_on(
    serial_number: str, input_number: int
):
    """Send input command to XP module or query status.

    Examples:

    \b
        xp conbus input on 0011223344 0  # Toggle input 0
    """
    service = ConbusInputService()

    with service:

        response = service.send_action(serial_number, input_number, ActionType.RELEASE)
        click.echo(json.dumps(response.to_dict(), indent=2))

@conbus_input.command("off")
@click.argument("serial_number", type=SERIAL)
@click.argument("input_number", type=int)
@connection_command()
@handle_service_errors(ConbusDatapointError)
def xp_input_off(
    serial_number: str, input_number: int
):
    """Send input command to XP module or query status.

    Examples:

    \b
        xp conbus input off 0011223344 1    # Toggle input 1
    """
    service = ConbusInputService()

    with service:

        response = service.send_action(serial_number, input_number, ActionType.RELEASE)
        click.echo(json.dumps(response, indent=2))

@conbus_input.command("status")
@click.argument("serial_number", type=SERIAL)
@connection_command()
@handle_service_errors(ConbusDatapointError)
def xp_input_status(
    serial_number: str
):
    """Send input command to XP module or query status.

    Examples:

    \b
        xp conbus input status 0011223344    # Query status
    """
    service = ConbusInputService()

    with service:

        response = service.send_status(serial_number)
        click.echo(json.dumps(response, indent=2))

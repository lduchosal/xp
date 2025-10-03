"""Conbus client operations CLI commands."""

import json

import click

from xp.cli.commands.conbus.conbus import conbus_output
from xp.cli.utils.decorators import (
    connection_command,
    handle_service_errors,
)
from xp.cli.utils.serial_number_type import SERIAL
from xp.models.telegram.action_type import ActionType
from xp.services.conbus.conbus_datapoint_service import (
    ConbusDatapointError,
)
from xp.services.conbus.conbus_output_service import ConbusOutputService


@conbus_output.command("on")
@click.argument("serial_number", type=SERIAL)
@click.argument("output_number", type=int)
@click.pass_context
@connection_command()
@handle_service_errors(ConbusDatapointError)
def xp_output_on(ctx: click.Context, serial_number: str, output_number: int) -> None:
    """Send ON command for output_number XP module serial_number

    Examples:

    \b
        xp conbus input on 0011223344 0  # Toggle input 0
    """
    service = ctx.obj.get("container").get_container().resolve(ConbusOutputService)

    with service:

        response = service.send_action(
            serial_number, output_number, ActionType.ON_RELEASE
        )
        click.echo(json.dumps(response.to_dict(), indent=2))


@conbus_output.command("off")
@click.argument("serial_number", type=SERIAL)
@click.argument("output_number", type=int)
@click.pass_context
@connection_command()
@handle_service_errors(ConbusDatapointError)
def xp_output_off(ctx: click.Context, serial_number: str, output_number: int) -> None:
    """Send OFF command for output_number XP module serial_number

    Examples:

    \b
        xp conbus input off 0011223344 1    # Toggle input 1
    """
    service = ctx.obj.get("container").get_container().resolve(ConbusOutputService)

    with service:

        response = service.send_action(
            serial_number, output_number, ActionType.OFF_PRESS
        )
        click.echo(json.dumps(response.to_dict(), indent=2))


@conbus_output.command("status")
@click.argument("serial_number", type=SERIAL)
@click.pass_context
@connection_command()
@handle_service_errors(ConbusDatapointError)
def xp_output_status(ctx: click.Context, serial_number: str) -> None:
    """Query output state command to XP module serial_number.

    Examples:

    \b
        xp conbus output status 0011223344    # Query output status
    """
    service = ctx.obj.get("container").get_container().resolve(ConbusOutputService)

    with service:

        response = service.get_output_state(serial_number)
        click.echo(json.dumps(response.to_dict(), indent=2))


@conbus_output.command("state")
@click.argument("serial_number", type=SERIAL)
@click.pass_context
@connection_command()
@handle_service_errors(ConbusDatapointError)
def xp_module_state(ctx: click.Context, serial_number: str) -> None:
    """Query module state of the XP module serial_number

    Examples:

    \b
        xp conbus output state 0011223344    # Query module state
    """
    service = ctx.obj.get("container").get_container().resolve(ConbusOutputService)

    with service:

        response = service.get_module_state(serial_number)
        click.echo(json.dumps(response.to_dict(), indent=2))

"""Conbus client operations CLI commands."""

import json

import click

from xp.cli.commands.conbus.conbus import conbus_output
from xp.cli.utils.decorators import (
    connection_command,
)
from xp.cli.utils.serial_number_type import SERIAL
from xp.models import ConbusDatapointResponse
from xp.models.conbus.conbus_output import ConbusOutputResponse
from xp.models.telegram.action_type import ActionType
from xp.models.telegram.datapoint_type import DataPointType
from xp.services.conbus.conbus_datapoint_service import ConbusDatapointService
from xp.services.conbus.conbus_output_service import ConbusOutputService


@conbus_output.command("on")
@click.argument("serial_number", type=SERIAL)
@click.argument("output_number", type=int)
@click.pass_context
@connection_command()
def xp_output_on(ctx: click.Context, serial_number: str, output_number: int) -> None:
    r"""Send ON command for output_number XP module serial_number.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.
        output_number: Output number.

    Examples:
        \b
        xp conbus output on 0011223344 0  # Turn on output 0
    """
    service: ConbusOutputService = (
        ctx.obj.get("container").get_container().resolve(ConbusOutputService)
    )

    def on_finish(response: ConbusOutputResponse) -> None:
        """Handle successful completion of output on command.

        Args:
            response: Output response object.
        """
        click.echo(json.dumps(response.to_dict(), indent=2))

    with service:
        service.send_action(
            serial_number=serial_number,
            output_number=output_number,
            action_type=ActionType.ON_RELEASE,
            finish_callback=on_finish,
        )


@conbus_output.command("off")
@click.argument("serial_number", type=SERIAL)
@click.argument("output_number", type=int)
@click.pass_context
@connection_command()
def xp_output_off(ctx: click.Context, serial_number: str, output_number: int) -> None:
    r"""Send OFF command for output_number XP module serial_number.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.
        output_number: Output number.

    Examples:
        \b
        xp conbus output off 0011223344 1    # Turn off output 1
    """
    service: ConbusOutputService = (
        ctx.obj.get("container").get_container().resolve(ConbusOutputService)
    )

    def on_finish(response: ConbusOutputResponse) -> None:
        """Handle successful completion of output off command.

        Args:
            response: Output response object.
        """
        click.echo(json.dumps(response.to_dict(), indent=2))

    with service:
        service.send_action(
            serial_number=serial_number,
            output_number=output_number,
            action_type=ActionType.OFF_PRESS,
            finish_callback=on_finish,
        )


@conbus_output.command("status")
@click.argument("serial_number", type=SERIAL)
@click.pass_context
@connection_command()
def xp_output_status(ctx: click.Context, serial_number: str) -> None:
    r"""Query output state command to XP module serial_number.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.

    Examples:
        \b
        xp conbus output status 0011223344    # Query output status
    """
    service: ConbusDatapointService = (
        ctx.obj.get("container").get_container().resolve(ConbusDatapointService)
    )

    def on_finish(response: ConbusDatapointResponse) -> None:
        """Handle successful completion of output status query.

        Args:
            response: Datapoint response object.
        """
        click.echo(json.dumps(response.to_dict(), indent=2))

    with service:
        service.query_datapoint(
            serial_number=serial_number,
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
            finish_callback=on_finish,
        )


@conbus_output.command("state")
@click.argument("serial_number", type=SERIAL)
@click.pass_context
@connection_command()
def xp_module_state(ctx: click.Context, serial_number: str) -> None:
    r"""Query module state of the XP module serial_number.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.

    Examples:
        \b
        xp conbus output state 0011223344    # Query module state
    """
    service: ConbusDatapointService = (
        ctx.obj.get("container").get_container().resolve(ConbusDatapointService)
    )

    def on_finish(response: ConbusDatapointResponse) -> None:
        """Handle successful completion of module state query.

        Args:
            response: Datapoint response object.
        """
        click.echo(json.dumps(response.to_dict(), indent=2))

    with service:
        service.query_datapoint(
            serial_number=serial_number,
            datapoint_type=DataPointType.MODULE_STATE,
            finish_callback=on_finish,
        )

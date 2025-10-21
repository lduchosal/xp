"""Conbus link number CLI commands."""

import json

import click

from xp.cli.commands.conbus.conbus import conbus_linknumber
from xp.cli.utils.decorators import (
    connection_command,
)
from xp.cli.utils.serial_number_type import SERIAL
from xp.models.conbus.conbus_linknumber import ConbusLinknumberResponse
from xp.models.conbus.conbus_writeconfig import ConbusWriteConfigResponse
from xp.models.telegram.datapoint_type import DataPointType
from xp.services.conbus.conbus_linknumber_get_service import ConbusLinknumberGetService
from xp.services.conbus.write_config_service import WriteConfigService


@conbus_linknumber.command("set", short_help="Set link number for a module")
@click.argument("serial_number", type=SERIAL)
@click.argument("link_number", type=click.IntRange(0, 99))
@click.pass_context
@connection_command()
def set_linknumber_command(
    ctx: click.Context, serial_number: str, link_number: int
) -> None:
    r"""Set the link number for a specific module.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.
        link_number: Link number to set (0-99).

    Examples:
        \b
        xp conbus linknumber set 0123450001 25
    """

    def finish(response: "ConbusWriteConfigResponse") -> None:
        """Handle successful completion of light level on command.

        Args:
            response: Light level response object.
        """
        click.echo(json.dumps(response.to_dict(), indent=2))

    service: WriteConfigService = (
        ctx.obj.get("container").get_container().resolve(WriteConfigService)
    )

    data_value = f"{link_number: 02d}"
    with service:
        service.write_config(
            serial_number=serial_number,
            datapoint_type=DataPointType.LINK_NUMBER,
            data_value=data_value,
            finish_callback=finish,
            timeout_seconds=0.5,
        )


@conbus_linknumber.command("get", short_help="Get link number for a module")
@click.argument("serial_number", type=SERIAL)
@click.pass_context
@connection_command()
def get_linknumber_command(ctx: click.Context, serial_number: str) -> None:
    r"""Get the current link number for a specific module.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.

    Examples:
        \b
        xp conbus linknumber get 0123450001
    """
    service = (
        ctx.obj.get("container").get_container().resolve(ConbusLinknumberGetService)
    )

    def on_finish(response: ConbusLinknumberResponse) -> None:
        """Handle successful completion of link number get command.

        Args:
            response: Link number response object.
        """
        click.echo(json.dumps(response.to_dict(), indent=2))

    with service:
        service.get_linknumber(
            serial_number=serial_number,
            finish_callback=on_finish,
        )

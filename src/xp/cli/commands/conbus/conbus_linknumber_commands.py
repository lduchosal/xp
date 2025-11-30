"""Conbus link number CLI commands."""

import json

import click

from xp.cli.commands.conbus.conbus import conbus_linknumber
from xp.cli.utils.decorators import (
    connection_command,
)
from xp.cli.utils.serial_number_type import SERIAL
from xp.models import ConbusDatapointResponse
from xp.models.conbus.conbus_writeconfig import ConbusWriteConfigResponse
from xp.models.telegram.datapoint_type import DataPointType
from xp.services.conbus.conbus_datapoint_service import ConbusDatapointService
from xp.services.conbus.write_config_service import WriteConfigService
from xp.services.telegram.telegram_datapoint_service import TelegramDatapointService


@conbus_linknumber.command("set", short_help="Set link number for a module")
@click.argument("serial_number", type=SERIAL)
@click.argument("link_number", type=click.IntRange(0, 99))
@click.pass_context
@connection_command()
def set_linknumber_command(
    ctx: click.Context, serial_number: str, link_number: int
) -> None:
    r"""
    Set the link number for a specific module.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.
        link_number: Link number to set (0-99).

    Examples:
        \b
        xp conbus linknumber set 0123450001 25
    """
    service: WriteConfigService = (
        ctx.obj.get("container").get_container().resolve(WriteConfigService)
    )

    def on_finish(response: "ConbusWriteConfigResponse") -> None:
        """
        Handle successful completion of light level on command.

        Args:
            response: Light level response object.
        """
        click.echo(json.dumps(response.to_dict(), indent=2))
        service.stop_reactor()

    data_value = f"{link_number:02d}"
    with service:
        service.on_finish.connect(on_finish)
        service.write_config(
            serial_number=serial_number,
            datapoint_type=DataPointType.LINK_NUMBER,
            data_value=data_value,
            timeout_seconds=0.5,
        )
        service.start_reactor()


@conbus_linknumber.command("get", short_help="Get link number for a module")
@click.argument("serial_number", type=SERIAL)
@click.pass_context
@connection_command()
def get_linknumber_command(ctx: click.Context, serial_number: str) -> None:
    r"""
    Get the current link number for a specific module.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.

    Examples:
        \b
        xp conbus linknumber get 0123450001
    """
    service: ConbusDatapointService = (
        ctx.obj.get("container").get_container().resolve(ConbusDatapointService)
    )
    telegram_service: TelegramDatapointService = (
        ctx.obj.get("container").get_container().resolve(TelegramDatapointService)
    )

    def on_finish(service_response: ConbusDatapointResponse) -> None:
        """
        Handle successful completion of link number get command.

        Args:
            service_response: Link number response object.
        """
        linknumber_value = telegram_service.get_linknumber(service_response.data_value)
        result = service_response.to_dict()
        result["linknumber_value"] = linknumber_value
        click.echo(json.dumps(result, indent=2))
        service.stop_reactor()

    with service:
        service.on_finish.connect(on_finish)
        service.query_datapoint(
            serial_number=serial_number,
            datapoint_type=DataPointType.LINK_NUMBER,
            timeout_seconds=0.5,
        )
        service.start_reactor()

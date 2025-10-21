"""Conbus lightlevel operations CLI commands."""

import json

import click

from xp.cli.commands.conbus.conbus import conbus_lightlevel
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


@conbus_lightlevel.command("set")
@click.argument("serial_number", type=SERIAL)
@click.argument("output_number", type=click.IntRange(0, 8))
@click.argument("level", type=click.IntRange(0, 100))
@click.pass_context
@connection_command()
def xp_lightlevel_set(
    ctx: click.Context, serial_number: str, output_number: int, level: int
) -> None:
    r"""Set light level for output_number on XP module serial_number.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.
        output_number: Output number (0-8).
        level: Light level (0-100).

    Examples:
        \b
        xp conbus lightlevel set 0123450001 2 50   # Set output 2 to 50%
        xp conbus lightlevel set 0011223344 0 100  # Set output 0 to 100%
    """

    def on_finish(response: "ConbusWriteConfigResponse") -> None:
        """Handle successful completion of light level on command.

        Args:
            response: Light level response object.
        """
        click.echo(json.dumps(response.to_dict(), indent=2))

    service: WriteConfigService = (
        ctx.obj.get("container").get_container().resolve(WriteConfigService)
    )

    data_value = f"{output_number:02d}:{level:03d}"

    with service:
        service.write_config(
            serial_number=serial_number,
            datapoint_type=DataPointType.MODULE_LIGHT_LEVEL,
            data_value=data_value,
            finish_callback=on_finish,
            timeout_seconds=0.5,
        )


@conbus_lightlevel.command("off")
@click.argument("serial_number", type=SERIAL)
@click.argument("output_number", type=click.IntRange(0, 8))
@click.pass_context
@connection_command()
def xp_lightlevel_off(
    ctx: click.Context, serial_number: str, output_number: int
) -> None:
    r"""Turn off light for output_number on XP module serial_number (set level to 0).

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.
        output_number: Output number (0-8).

    Examples:
        \b
        xp conbus lightlevel off 0123450001 2   # Turn off output 2
        xp conbus lightlevel off 0011223344 0   # Turn off output 0
    """

    def on_finish(response: "ConbusWriteConfigResponse") -> None:
        """Handle successful completion of light level on command.

        Args:
            response: Light level response object.
        """
        click.echo(json.dumps(response.to_dict(), indent=2))

    service: WriteConfigService = (
        ctx.obj.get("container").get_container().resolve(WriteConfigService)
    )

    level = 0
    data_value = f"{output_number:02d}:{level:03d}"

    with service:
        service.write_config(
            serial_number=serial_number,
            datapoint_type=DataPointType.MODULE_LIGHT_LEVEL,
            data_value=data_value,
            finish_callback=on_finish,
            timeout_seconds=0.5,
        )


@conbus_lightlevel.command("on")
@click.argument("serial_number", type=SERIAL)
@click.argument("output_number", type=click.IntRange(0, 8))
@click.pass_context
@connection_command()
def xp_lightlevel_on(
    ctx: click.Context, serial_number: str, output_number: int
) -> None:
    r"""Turn on light for output_number on XP module serial_number (set level to 80%).

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.
        output_number: Output number (0-8).

    Examples:
        \b
        xp conbus lightlevel on 0123450001 2   # Turn on output 2 (80%)
        xp conbus lightlevel on 0011223344 0   # Turn on output 0 (80%)
    """

    def on_finish(response: "ConbusWriteConfigResponse") -> None:
        """Handle successful completion of light level on command.

        Args:
            response: Light level response object.
        """
        click.echo(json.dumps(response.to_dict(), indent=2))

    service: WriteConfigService = (
        ctx.obj.get("container").get_container().resolve(WriteConfigService)
    )

    level = 60
    data_value = f"{output_number:02d}:{level:03d}"

    with service:
        service.write_config(
            serial_number=serial_number,
            datapoint_type=DataPointType.MODULE_LIGHT_LEVEL,
            data_value=data_value,
            finish_callback=on_finish,
            timeout_seconds=0.5,
        )


@conbus_lightlevel.command("get")
@click.argument("serial_number", type=SERIAL)
@click.argument("output_number", type=click.IntRange(0, 8))
@click.pass_context
@connection_command()
def xp_lightlevel_get(
    ctx: click.Context, serial_number: str, output_number: int
) -> None:
    r"""Get current light level for output_number on XP module serial_number.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.
        output_number: Output number (0-8).

    Examples:
        \b
        xp conbus lightlevel get 0123450001 2   # Get light level for output 2
        xp conbus lightlevel get 0011223344 0   # Get light level for output 0
    """
    # Get service from container
    service: ConbusDatapointService = (
        ctx.obj.get("container").get_container().resolve(ConbusDatapointService)
    )
    telegram_service: TelegramDatapointService = (
        ctx.obj.get("container").get_container().resolve(TelegramDatapointService)
    )

    def on_finish(service_response: "ConbusDatapointResponse") -> None:
        """Handle successful completion of light level get command.

        Args:
            service_response: Light level response object.
        """
        lightlevel_level = telegram_service.get_lightlevel(
            service_response.data_value, output_number
        )
        result = service_response.to_dict()
        result["output_number"] = output_number
        result["lightlevel_level"] = lightlevel_level
        click.echo(json.dumps(result, indent=2))

    with service:
        service.query_datapoint(
            serial_number=serial_number,
            datapoint_type=DataPointType.MODULE_LIGHT_LEVEL,
            finish_callback=on_finish,
            timeout_seconds=0.5,
        )

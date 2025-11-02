"""Conbus module number CLI commands."""

import json

import click

from xp.cli.commands.conbus.conbus import conbus_modulenumber
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


@conbus_modulenumber.command("set", short_help="Set module number for a module")
@click.argument("serial_number", type=SERIAL)
@click.argument("module_number", type=click.IntRange(0, 99))
@click.pass_context
@connection_command()
def set_modulenumber_command(
    ctx: click.Context, serial_number: str, module_number: int
) -> None:
    r"""Set the module number for a specific module.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.
        module_number: Module number to set (0-99).

    Examples:
        \b
        xp conbus modulenumber set 0123450001 25
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

    data_value = f"{module_number:02d}"
    with service:
        service.write_config(
            serial_number=serial_number,
            datapoint_type=DataPointType.MODULE_NUMBER,
            data_value=data_value,
            finish_callback=on_finish,
            timeout_seconds=0.5,
        )


@conbus_modulenumber.command("get", short_help="Get module number for a module")
@click.argument("serial_number", type=SERIAL)
@click.pass_context
@connection_command()
def get_modulenumber_command(ctx: click.Context, serial_number: str) -> None:
    r"""Get the current module number for a specific module.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.

    Examples:
        \b
        xp conbus modulenumber get 0123450001
    """
    service: ConbusDatapointService = (
        ctx.obj.get("container").get_container().resolve(ConbusDatapointService)
    )
    telegram_service: TelegramDatapointService = (
        ctx.obj.get("container").get_container().resolve(TelegramDatapointService)
    )

    def on_finish(service_response: ConbusDatapointResponse) -> None:
        """Handle successful completion of module number get command.

        Args:
            service_response: Module number response object.
        """
        modulenumber_value = telegram_service.get_modulenumber(
            service_response.data_value
        )
        result = service_response.to_dict()
        result["modulenumber_value"] = modulenumber_value
        click.echo(json.dumps(result, indent=2))

    with service:
        service.query_datapoint(
            serial_number=serial_number,
            datapoint_type=DataPointType.MODULE_NUMBER,
            finish_callback=on_finish,
            timeout_seconds=0.5,
        )

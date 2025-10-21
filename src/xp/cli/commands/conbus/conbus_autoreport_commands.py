"""Conbus auto report CLI commands."""

import json

import click
from click import Context

from xp.cli.commands.conbus.conbus import conbus_autoreport
from xp.cli.utils.decorators import (
    connection_command,
)
from xp.cli.utils.serial_number_type import SERIAL
from xp.models.conbus.conbus_autoreport import ConbusAutoreportResponse
from xp.models.conbus.conbus_writeconfig import ConbusWriteConfigResponse
from xp.models.telegram.datapoint_type import DataPointType
from xp.services.conbus.conbus_autoreport_get_service import (
    ConbusAutoreportGetService,
)
from xp.services.conbus.write_config_service import WriteConfigService


@conbus_autoreport.command("get", short_help="Get auto report status for a module")
@click.argument("serial_number", type=SERIAL)
@connection_command()
@click.pass_context
def get_autoreport_command(ctx: Context, serial_number: str) -> None:
    r"""Get the current auto report status for a specific module.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.

    Examples:
        \b
        xp conbus autoreport get 0123450001
    """
    # Get service from container
    service: ConbusAutoreportGetService = (
        ctx.obj.get("container").get_container().resolve(ConbusAutoreportGetService)
    )

    def on_finish(service_response: ConbusAutoreportResponse) -> None:
        """Handle successful completion of auto report status retrieval.

        Args:
            service_response: Auto report response object.
        """
        click.echo(json.dumps(service_response.to_dict(), indent=2))

    with service:
        service.get_autoreport_status(
            serial_number=serial_number,
            finish_callback=on_finish,
        )


@conbus_autoreport.command("set", short_help="Set auto report status for a module")
@click.argument("serial_number", type=SERIAL)
@click.argument("status", type=click.Choice(["on", "off"], case_sensitive=False))
@connection_command()
@click.pass_context
def set_autoreport_command(ctx: Context, serial_number: str, status: str) -> None:
    r"""Set the auto report status for a specific module.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.
        status: Auto report status - either 'on' or 'off'.

    Examples:
        \b
        xp conbus autoreport set 0123450001 on
        xp conbus autoreport set 0123450001 off
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
    status_value = True if status == "on" else False
    data_value = "PP" if status_value else "AA"

    with service:
        service.write_config(
            serial_number=serial_number,
            datapoint_type=DataPointType.AUTO_REPORT_STATUS,
            data_value=data_value,
            finish_callback=finish,
            timeout_seconds=0.5,
        )

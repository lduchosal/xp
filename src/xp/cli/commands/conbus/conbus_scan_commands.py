"""Conbus client operations CLI commands."""

import json

import click
from click import Context

from xp.cli.commands.conbus.conbus import conbus
from xp.cli.utils.decorators import connection_command
from xp.cli.utils.serial_number_type import SERIAL
from xp.models import ConbusResponse
from xp.services.conbus.conbus_scan_service import ConbusScanService


@conbus.command("scan")
@click.argument("serial_number", type=SERIAL)
@click.argument("function_code", type=str)
@click.pass_context
@connection_command()
def scan_module(ctx: Context, serial_number: str, function_code: str) -> None:
    r"""Scan all datapoints of a function_code for a module.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.
        function_code: Function code.

    Examples:
        \b
        xp conbus scan 0012345011 02 # Scan all datapoints of function Read data points (02)
    """
    service: ConbusScanService = (
        ctx.obj.get("container").get_container().resolve(ConbusScanService)
    )

    def on_progress(progress: str) -> None:
        """Handle progress updates during module scan.

        Args:
            progress: Progress message string.
        """
        click.echo(progress)

    def on_finish(service_response: ConbusResponse) -> None:
        """Handle successful completion of module scan.

        Args:
            service_response: Scan response object.
        """
        click.echo(json.dumps(service_response.to_dict(), indent=2))

    with service:
        service.scan_module(
            serial_number=serial_number,
            function_code=function_code,
            progress_callback=on_progress,
            finish_callback=on_finish,
        )

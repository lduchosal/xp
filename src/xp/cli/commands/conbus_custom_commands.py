"""Conbus client operations CLI commands."""

import json

import click

from .conbus import conbus
from ..utils.decorators import (
    connection_command,
    handle_service_errors,
)
from ..utils.error_handlers import CLIErrorHandler
from ..utils.serial_number_type import SERIAL
from ...models.system_function import SystemFunction
from ...services.conbus_datapoint_service import (
    ConbusDatapointError,
)
from ...services.conbus_service import ConbusService


@conbus.command("custom")
@click.argument("serial_number", type=SERIAL)
@click.argument("system_function")
@click.argument("datapoint_code")
@connection_command()
@handle_service_errors(ConbusDatapointError)
def send_custom_telegram(
    serial_number: str, system_function: SystemFunction, datapoint_code: str
):
    """
    Send custom telegram with specified function and data point codes.

    Examples:

    \b
        xp conbus custom 0020030837 02 E2
        xp conbus custom 0020030837 17 AA
    """
    service = ConbusService()

    try:
        with service:
            response = service.send_telegram(
                serial_number, system_function, datapoint_code
            )

        click.echo(json.dumps(response.to_dict(), indent=2))

    except ConbusDatapointError as e:
        CLIErrorHandler.handle_service_error(e, "custom telegram send", {
            "serial_number": serial_number,
            "system_function": system_function,
            "datapoint_code": datapoint_code,
        })

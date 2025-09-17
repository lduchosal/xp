"""Conbus client operations CLI commands."""

import click
import json

from ...services.conbus_client_send_service import (
    ConbusClientSendService,
    ConbusClientSendError,
)
from ..utils.decorators import (
    connection_command,
    handle_service_errors,
)
from ..utils.error_handlers import CLIErrorHandler
from ..utils.serial_number_type import SERIAL
from .conbus import conbus


@conbus.command("custom")
@click.argument("serial_number", type=SERIAL)
@click.argument("function_code")
@click.argument("data_point_code")
@connection_command()
@handle_service_errors(ConbusClientSendError)
def send_custom_telegram(
    serial_number: str, function_code: str, data_point_code: str
):
    """
    Send custom telegram with specified function and data point codes.

    Examples:

    \b
        xp conbus custom 0020030837 02 E2
        xp conbus custom 0020030837 17 AA
    """
    service = ConbusClientSendService()

    try:
        with service:
            response = service.send_custom_telegram(
                serial_number, function_code, data_point_code
            )

        click.echo(json.dumps(response.to_dict(), indent=2))

    except ConbusClientSendError as e:
        CLIErrorHandler.handle_service_error(e, "custom telegram send", {
            "serial_number": serial_number,
            "function_code": function_code,
            "data_point_code": data_point_code,
        })

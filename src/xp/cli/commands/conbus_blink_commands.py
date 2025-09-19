"""Conbus client operations CLI commands."""

import json

import click

from .conbus import conbus_blink
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
from ...services.telegram_blink_service import BlinkService, BlinkError


@conbus_blink.command("on", short_help="Blink on remote service")
@click.argument("serial_number", type=SERIAL)
@connection_command()
@handle_service_errors(ConbusDatapointError, BlinkError)
def send_blink_on_telegram(serial_number: str):
    """
    Send blink command to start blinking module LED.

    Examples:

    \b
        xp conbus blink on 0020044964
    """
    send_blink_telegram(serial_number, 'on')

@conbus_blink.command("off")
@click.argument("serial_number", type=SERIAL)
@connection_command()
@handle_service_errors(ConbusDatapointError, BlinkError)
def send_blink_off_telegram(serial_number: str):
    """
    Send blink command to start blinking module LED.

    Examples:

    \b
        xp conbus blink off 0020044964
    """
    send_blink_telegram(serial_number, 'off')

def send_blink_telegram(serial_number: str, on_or_off: str):

    """
    Send blink command to start blinking module LED.

    Examples:

    \b
        xp conbus blink 0020044964 on
        xp conbus blink 0020044964 off
    """
    conbus_service = ConbusService()
    blink_service = BlinkService()

    # Blink is 05, Unblink is 06
    system_function = SystemFunction.UNBLINK
    operation = "unblink"
    if on_or_off.lower() == "on":
        system_function = SystemFunction.BLINK
        operation = "blink"

    try:
        # Validate serial number using blink service
        blink_service.generate_blink_telegram(
            serial_number,
            on_or_off
        )  # This validates the serial

        # Send blink telegram using custom method (F05D00)
        with conbus_service:
            response = conbus_service.send_telegram(
                serial_number,
                system_function,  # Blink or Unblink function code
                "00",  # Status data point
            )

        response_data = response.to_dict()
        response_data["operation"] = operation
        response_data["on_or_off"] = on_or_off
        click.echo(json.dumps(response_data, indent=2))

    except BlinkError as e:
        error_response = {
            "success": False,
            "error": str(e),
            "operation": operation,
            "serial_number": serial_number,
        }
        click.echo(json.dumps(error_response, indent=2))
        raise SystemExit(1)

    except ConbusDatapointError as e:
        CLIErrorHandler.handle_service_error(
            e,
            "blink command",
            {"serial_number": serial_number, "operation": operation})


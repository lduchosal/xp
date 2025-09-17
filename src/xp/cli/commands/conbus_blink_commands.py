"""Conbus client operations CLI commands."""

import click
import json

from ...models.system_function import SystemFunction
from ...services.conbus_client_send_service import (
    ConbusClientSendService,
    ConbusClientSendError,
)
from ...services.telegram_blink_service import BlinkService, BlinkError
from ..utils.decorators import (
    connection_command,
    handle_service_errors,
)
from ..utils.error_handlers import CLIErrorHandler
from ..utils.serial_number_type import SERIAL
from .conbus import conbus


@conbus.command("blink")
@click.argument("serial_number", type=SERIAL)
@click.argument("on_or_off", type=click.Choice(["on", "off"]), default="on")
@connection_command()
@handle_service_errors(ConbusClientSendError, BlinkError)
def send_blink_telegram(serial_number: str, on_or_off: str):
    """
    Send blink command to start blinking module LED.

    Examples:

    \b
        xp conbus blink 0020044964 on
        xp conbus blink 0020044964 off
    """
    conbus_service = ConbusClientSendService()
    blink_service = BlinkService()

    # Blink is 05, Unblink is 06
    function_code = SystemFunction.UNBLINK.value
    operation = "unblink"
    blink_operation = "stop_blinking"
    blink_value = False
    if on_or_off.lower() == "on":
        function_code = SystemFunction.BLINK.value
        operation = "blink"
        blink_operation = "start_blinking"
        blink_value = True

    try:
        # Validate serial number using blink service
        blink_service.generate_blink_telegram(
            serial_number,
            blink_value
        )  # This validates the serial

        # Send blink telegram using custom method (F05D00)
        with conbus_service:
            response = conbus_service.send_custom_telegram(
                serial_number,
                function_code,  # Blink or Unblink function code
                "00",  # Status data point
            )

        response_data = response.to_dict()
        response_data["operation"] = operation
        response_data["blink_operation"] = blink_operation
        response_data["blink_value"] = blink_value
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

    except ConbusClientSendError as e:
        CLIErrorHandler.handle_service_error(e, "blink command",
                                             {"serial_number": serial_number, "operation": operation})

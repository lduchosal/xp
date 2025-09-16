"""Conbus client operations CLI commands."""


import click
import json

from ...models.system_function import SystemFunction
from ...services.conbus_client_send_service import (
    ConbusClientSendService,
    ConbusClientSendError,
)
from ...services.blink_service import BlinkService, BlinkError
from ..utils.decorators import (
    connection_command,
    handle_service_errors,
)
from ..utils.error_handlers import CLIErrorHandler


@click.group()
def conbus():
    """Conbus client operations for sending telegrams to remote servers"""
    pass


@conbus.command("blink")
@click.argument("serial_number")
@click.argument("on_or_off")
@connection_command()
@handle_service_errors(ConbusClientSendError, BlinkError)
def send_blink_telegram(serial_number: str, on_or_off: str, json_output: bool):
    """
    Send blink command to start blinking module LED.

    Example: xp conbus blink 0020044964 on
    Example: xp conbus blink 0020044964 off
    """
    conbus_service = ConbusClientSendService()
    blink_service = BlinkService()

    # Blink is 05, Unblink is 06
    function_code = SystemFunction.UNBLINK.value
    operation = "unblink"
    blink_operation = "stop_blinking"
    if on_or_off.lower() == "on":
        function_code = SystemFunction.BLINK.value
        operation = "blink"
        blink_operation = "start_blinking"

    try:
        # Validate serial number using blink service
        blink_service.generate_blink_telegram(
            serial_number
        )  # This validates the serial

        # Send blink telegram using custom method (F05D00)
        with conbus_service:
            response = conbus_service.send_custom_telegram(
                serial_number,
                function_code,  # Blink or Unblink function code
                "00",  # Status data point
            )

        if json_output:
            response_data = response.to_dict()
            response_data["operation"] = operation
            response_data["blink_operation"] = blink_operation
            click.echo(json.dumps(response_data, indent=2))
        else:
            if response.success:
                # Format output like other conbus commands
                if response.sent_telegram:
                    timestamp = response.timestamp.strftime("%H:%M:%S,%f")[:-3]
                    click.echo(f"{timestamp} [TX] {response.sent_telegram}")

                # Show received telegrams
                for received in response.received_telegrams:
                    timestamp = response.timestamp.strftime("%H:%M:%S,%f")[:-3]
                    click.echo(f"{timestamp} [RX] {received}")

                if not response.received_telegrams:
                    click.echo("No response received")
                else:
                    click.echo(f"Blink command sent to module {serial_number}")
            else:
                click.echo(f"Error: {response.error}")

    except BlinkError as e:
        if json_output:
            error_response = {
                "success": False,
                "error": str(e),
                "operation": operation,
                "serial_number": serial_number,
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"Blink Error: {e}", err=True)
            raise click.ClickException(str(e))

    except ConbusClientSendError as e:
        CLIErrorHandler.handle_service_error(
            e,
            json_output,
            "blink command",
            {"serial_number": serial_number, "operation": operation},
        )

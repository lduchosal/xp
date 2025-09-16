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


@click.group()
def conbus():
    """Conbus client operations for sending telegrams to remote servers"""
    pass


@conbus.command("custom")
@click.argument("serial_number")
@click.argument("function_code")
@click.argument("data_point_code")
@connection_command()
@handle_service_errors(ConbusClientSendError)
def send_custom_telegram(
    serial_number: str, function_code: str, data_point_code: str, json_output: bool
):
    """
    Send custom telegram with specified function and data point codes.

    Example: xp conbus custom 0020030837 02 E2
    """
    service = ConbusClientSendService()

    try:
        with service:
            response = service.send_custom_telegram(
                serial_number, function_code, data_point_code
            )

        if json_output:
            click.echo(json.dumps(response.to_dict(), indent=2))
        else:
            if response.success:
                # Format output like the specification examples
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
                click.echo(f"Error: {response.error}")

    except ConbusClientSendError as e:
        CLIErrorHandler.handle_service_error(
            e,
            json_output,
            "custom telegram send",
            {
                "serial_number": serial_number,
                "function_code": function_code,
                "data_point_code": data_point_code,
            },
        )

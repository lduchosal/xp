"""Conbus client operations CLI commands."""

import click
import json

from ...services.conbus_client_send_service import (
    ConbusClientSendService,
    ConbusClientSendError,
)
from ...models import ConbusSendRequest, TelegramType
from ..utils.decorators import (
    connection_command,
    handle_service_errors,
)
from ..utils.formatters import OutputFormatter
from ..utils.error_handlers import CLIErrorHandler
from .conbus import conbus


@conbus.command("discover")
@connection_command()
@handle_service_errors(ConbusClientSendError)
def send_discover_telegram(json_output: bool):
    """
    Send discovery telegram to Conbus server.

    Examples:

    \b
        xp conbus discover
    """
    service = ConbusClientSendService()

    try:
        # Discovery telegram
        telegram_type_enum = TelegramType.DISCOVERY
        target_serial = None

        # Create request
        request = ConbusSendRequest(
            telegram_type=telegram_type_enum, target_serial=target_serial
        )

        # Send telegram
        with service:
            response = service.send_telegram(request)

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
        if "Connection timeout" in str(e):
            if not json_output:
                click.echo(
                    f"Connecting to {service.config.ip}:{service.config.port}..."
                )
                click.echo(
                    f"Error: Connection timeout after {service.config.timeout} seconds"
                )
                click.echo("Failed to connect to server")
            CLIErrorHandler.handle_connection_error(
                e,
                json_output,
                {
                    "ip": service.config.ip,
                    "port": service.config.port,
                    "timeout": service.config.timeout,
                },
            )
        else:
            CLIErrorHandler.handle_service_error(
                e, json_output, "discovery telegram send"
            )

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


@conbus.command("send")
@click.argument("target_serial")
@click.argument("telegram_type")
@connection_command()
@handle_service_errors(ConbusClientSendError)
def send_telegram(target_serial: str, telegram_type: str, json_output: bool):
    """
    Send telegram to Conbus server.

    Examples:
    xp conbus send 0000000000 discovery
    xp conbus send 0020030837 version
    xp conbus send 0020030837 voltage
    xp conbus send 0020030837 temperature
    xp conbus send 0020030837 current
    xp conbus send 0020030837 humidity
    """
    service = ConbusClientSendService()
    formatter = OutputFormatter(json_output)

    try:
        # Validate arguments
        if target_serial is None:
            error_response = formatter.error_response("target_serial is required")
            if json_output:
                click.echo(error_response)
                raise SystemExit(1)
            else:
                click.echo("Error: target_serial is required", err=True)
                raise click.ClickException("Missing target_serial")

        if telegram_type is None:
            error_response = formatter.error_response("Telegram type required")
            if json_output:
                click.echo(error_response)
                raise SystemExit(1)
            else:
                click.echo("Error: Telegram type required", err=True)
                raise click.ClickException("Missing telegram type")

        # Map string to enum
        telegram_type_map = {
            "discovery": TelegramType.DISCOVERY,
            "version": TelegramType.VERSION,
            "voltage": TelegramType.VOLTAGE,
            "temperature": TelegramType.TEMPERATURE,
            "current": TelegramType.CURRENT,
            "humidity": TelegramType.HUMIDITY,
        }

        telegram_type_enum = telegram_type_map.get(telegram_type.lower())
        if not telegram_type_enum:
            error_data = {
                "telegram_type": telegram_type,
                "valid_types": list(telegram_type_map.keys()),
            }
            error_response = formatter.error_response(
                f"Unknown telegram type: {telegram_type}", error_data
            )

            if json_output:
                click.echo(error_response)
                raise SystemExit(1)
            else:
                click.echo(f"Error: Unknown telegram type: {telegram_type}", err=True)
                click.echo(f"Valid types: {', '.join(telegram_type_map.keys())}")
                raise click.ClickException("Invalid telegram type")

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
            CLIErrorHandler.handle_service_error(e, json_output, "telegram send")


@conbus.command("discover")
@connection_command()
@handle_service_errors(ConbusClientSendError)
def send_discover_telegram(json_output: bool):
    """
    Send discovery telegram to Conbus server.

    Examples:
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

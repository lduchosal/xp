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
def send_telegram(target_serial: str, telegram_type: str):
    """
    Send telegram to Conbus server.

    Examples:

    \b
        xp conbus send 0000000000 discovery
        xp conbus send 0020030837 version
        xp conbus send 0020030837 voltage
        xp conbus send 0020030837 temperature
        xp conbus send 0020030837 current
        xp conbus send 0020030837 humidity
    """
    service = ConbusClientSendService()
    formatter = OutputFormatter(True)

    try:
        # Validate arguments
        if target_serial is None:
            error_response = formatter.error_response("target_serial is required")
            click.echo(error_response)
            raise SystemExit(1)

        if telegram_type is None:
            error_response = formatter.error_response("Telegram type required")
            click.echo(error_response)
            raise SystemExit(1)

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

            click.echo(error_response)
            raise SystemExit(1)

        # Create request
        request = ConbusSendRequest(
            telegram_type=telegram_type_enum, target_serial=target_serial
        )

        # Send telegram
        with service:
            response = service.send_telegram(request)

        click.echo(json.dumps(response.to_dict(), indent=2))

    except ConbusClientSendError as e:
        if "Connection timeout" in str(e):
            CLIErrorHandler.handle_connection_error(
                e,
                True,
                {
                    "ip": service.config.ip,
                    "port": service.config.port,
                    "timeout": service.config.timeout,
                },
            )
        else:
            CLIErrorHandler.handle_service_error(e, "telegram send")

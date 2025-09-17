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
def send_discover_telegram():
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
            CLIErrorHandler.handle_service_error(e, "discovery telegram send")

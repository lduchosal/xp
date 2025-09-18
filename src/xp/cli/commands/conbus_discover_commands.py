"""Conbus client operations CLI commands."""

import click
import json

from ...services.conbus_discover_service import (
    ConbusDiscoverService,
    ConbusDiscoverRequest,
    ConbusDiscoverError,
)
from ...models import ConbusDatapointRequest, DatapointTypeName
from ..utils.decorators import (
    connection_command,
    handle_service_errors,
)
from ..utils.error_handlers import CLIErrorHandler
from .conbus import conbus


@conbus.command("discover")
@connection_command()
@handle_service_errors(ConbusDiscoverError)
def send_discover_telegram():
    """
    Send discovery telegram to Conbus server.

    Examples:

    \b
        xp conbus discover
    """
    service = ConbusDiscoverService()

    try:
        # Discovery telegram
        request = ConbusDiscoverRequest()

        # Send telegram
        with service:
            response = service.send_telegram(request)

        click.echo(json.dumps(response.to_dict(), indent=2))

    except ConbusDiscoverError as e:
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

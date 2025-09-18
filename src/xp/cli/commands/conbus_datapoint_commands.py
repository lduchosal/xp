"""Conbus client operations CLI commands."""

import click
import json

from ..utils.serial_number_type import SERIAL
from ..utils.datapoint_type_name_choice import DATAPOINT
from ...services.conbus_datapoint_service import (
    ConbusDatapointService,
    ConbusDatapointError,
)
from ...models import ConbusDatapointRequest, DatapointTypeName
from ..utils.decorators import (
    connection_command,
    handle_service_errors,
)
from ..utils.formatters import OutputFormatter
from ..utils.error_handlers import CLIErrorHandler
from .conbus import conbus


@conbus.command("datapoint")
@click.argument("datapoint", type=DATAPOINT)
@click.argument("target_serial", type=SERIAL)
@connection_command()
@handle_service_errors(ConbusDatapointError)
def datapoint_telegram(target_serial: str, datapoint: DatapointTypeName):
    """
    Send telegram to Conbus server.

    Examples:

    \b
        xp conbus datapoint version 0020030837
        xp conbus datapoint voltage 0020030837
        xp conbus datapoint temperature 0020030837
        xp conbus datapoint current 0020030837
        xp conbus datapoint humidity 0020030837
    """
    service = ConbusDatapointService()
    formatter = OutputFormatter(True)

    try:
        # Validate arguments
        if target_serial is None:
            error_response = formatter.error_response("target_serial is required")
            click.echo(error_response)
            raise SystemExit(1)

        if datapoint is None:
            error_response = formatter.error_response("Datapoint is required")
            click.echo(error_response)
            raise SystemExit(1)

        # Create request
        request = ConbusDatapointRequest(
            datapoint_type=datapoint, target_serial=target_serial
        )

        # Send telegram
        with service:
            response = service.send_telegram(request)

        click.echo(json.dumps(response.to_dict(), indent=2))

    except ConbusDatapointError as e:
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

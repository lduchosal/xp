"""Conbus client operations CLI commands."""

import json

import click

from .conbus import conbus_blink
from ..utils.decorators import (
    connection_command,
    handle_service_errors,
)
from ..utils.serial_number_type import SERIAL
from ...services.conbus_blink_service import ConbusBlinkService
from ...services.conbus_datapoint_service import (
    ConbusDatapointError,
)
from ...services.telegram_blink_service import BlinkError


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
    service = ConbusBlinkService()

    with service:

        response = service.send_blink_telegram(serial_number, 'on')
        click.echo(json.dumps(response.to_dict(), indent=2))


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
    service = ConbusBlinkService()

    with service:

        response = service.send_blink_telegram(serial_number, 'off')
        click.echo(json.dumps(response.to_dict(), indent=2))


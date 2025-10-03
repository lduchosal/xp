"""Conbus client operations CLI commands."""

import json

import click
from click import Context

from xp.cli.commands.conbus.conbus import conbus_blink
from xp.cli.utils.decorators import (
    connection_command,
    handle_service_errors,
)
from xp.cli.utils.serial_number_type import SERIAL
from xp.services.conbus.conbus_blink_service import ConbusBlinkService
from xp.services.conbus.conbus_datapoint_service import (
    ConbusDatapointError,
)
from xp.services.telegram.telegram_blink_service import BlinkError


@conbus_blink.command("on", short_help="Blink on remote service")
@click.argument("serial_number", type=SERIAL)
@click.pass_context
@connection_command()
@handle_service_errors(ConbusDatapointError, BlinkError)
def send_blink_on_telegram(ctx: Context, serial_number: str) -> None:
    """
    Send blink command to start blinking module LED.

    Examples:

    \b
        xp conbus blink on 0012345008
    """
    service = ctx.obj.get("container").get_container().resolve(ConbusBlinkService)

    with service:

        response = service.send_blink_telegram(serial_number, "on")
        click.echo(json.dumps(response.to_dict(), indent=2))


@conbus_blink.command("off")
@click.argument("serial_number", type=SERIAL)
@click.pass_context
@connection_command()
@handle_service_errors(ConbusDatapointError, BlinkError)
def send_blink_off_telegram(ctx: Context, serial_number: str) -> None:
    """
    Send blink command to start blinking module LED.

    Examples:

    \b
        xp conbus blink off 0012345008
    """
    service = ctx.obj.get("container").get_container().resolve(ConbusBlinkService)

    with service:

        response = service.send_blink_telegram(serial_number, "off")
        click.echo(json.dumps(response.to_dict(), indent=2))


@conbus_blink.group("all", short_help="Control blink state for all devices")
def conbus_blink_all() -> None:
    """
    Control blink state for all discovered devices.
    """
    pass


@conbus_blink_all.command("off", short_help="Turn off blinking for all devices")
@click.pass_context
@connection_command()
@handle_service_errors(ConbusDatapointError, BlinkError)
def blink_all_off(ctx: Context) -> None:
    """
    Turn off blinking for all discovered devices.

    Examples:

    \b
        xp conbus blink all off
    """
    service = ctx.obj.get("container").get_container().resolve(ConbusBlinkService)

    with service:
        response = service.blink_all("off")
        if response.success:
            click.echo("All devices blink turned off")
        else:
            click.echo(f"Error: {response.error}")


@conbus_blink_all.command("on", short_help="Turn on blinking for all devices")
@click.pass_context
@connection_command()
@handle_service_errors(ConbusDatapointError, BlinkError)
def blink_all_on(ctx: Context) -> None:
    """
    Turn on blinking for all discovered devices.

    Examples:

    \b
        xp conbus blink all on
    """
    service = ctx.obj.get("container").get_container().resolve(ConbusBlinkService)

    with service:
        response = service.blink_all("on")
        if response.success:
            click.echo("All devices blink turned on")
        else:
            click.echo(f"Error: {response.error}")

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
from xp.models.conbus.conbus_blink import ConbusBlinkResponse
from xp.services.conbus.conbus_blink_all_service import ConbusBlinkAllService
from xp.services.conbus.conbus_blink_service import ConbusBlinkService
from xp.services.telegram.telegram_blink_service import BlinkError


@conbus_blink.command("on", short_help="Blink on remote service")
@click.argument("serial_number", type=SERIAL)
@click.pass_context
@connection_command()
@handle_service_errors(BlinkError)
def send_blink_on_telegram(ctx: Context, serial_number: str) -> None:
    r"""Send blink command to start blinking module LED.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.

    Examples:
        \b
        xp conbus blink on 0012345008
    """

    def on_finish(service_response: ConbusBlinkResponse) -> None:
        """Handle successful completion of blink on command.

        Args:
            service_response: Blink response object.
        """
        click.echo(json.dumps(service_response.to_dict(), indent=2))

    service: ConbusBlinkService = (
        ctx.obj.get("container").get_container().resolve(ConbusBlinkService)
    )
    with service:
        service.send_blink_telegram(serial_number, "on", on_finish, 0.5)


@conbus_blink.command("off")
@click.argument("serial_number", type=SERIAL)
@click.pass_context
@connection_command()
@handle_service_errors(BlinkError)
def send_blink_off_telegram(ctx: Context, serial_number: str) -> None:
    r"""Send blink command to stop blinking module LED.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.

    Examples:
        \b
        xp conbus blink off 0012345008
    """

    def on_finish(service_response: ConbusBlinkResponse) -> None:
        """Handle successful completion of blink off command.

        Args:
            service_response: Blink response object.
        """
        click.echo(json.dumps(service_response.to_dict(), indent=2))

    service: ConbusBlinkService = (
        ctx.obj.get("container").get_container().resolve(ConbusBlinkService)
    )
    with service:
        service.send_blink_telegram(serial_number, "off", on_finish, 0.5)


@conbus_blink.group("all", short_help="Control blink state for all devices")
def conbus_blink_all() -> None:
    """Control blink state for all discovered devices."""
    pass


@conbus_blink_all.command("off", short_help="Turn off blinking for all devices")
@click.pass_context
@connection_command()
@handle_service_errors(BlinkError)
def blink_all_off(ctx: Context) -> None:
    r"""Turn off blinking for all discovered devices.

    Args:
        ctx: Click context object.

    Examples:
        \b
        xp conbus blink all off
    """

    def on_finish(discovered_devices: ConbusBlinkResponse) -> None:
        """Handle successful completion of blink all off command.

        Args:
            discovered_devices: Blink response with all devices.
        """
        click.echo(json.dumps(discovered_devices.to_dict(), indent=2))

    def progress(message: str) -> None:
        """Handle progress updates during blink all off operation.

        Args:
            message: Progress message string.
        """
        click.echo(message)

    service: ConbusBlinkAllService = (
        ctx.obj.get("container").get_container().resolve(ConbusBlinkAllService)
    )
    with service:
        service.send_blink_all_telegram("off", progress, on_finish, 0.5)


@conbus_blink_all.command("on", short_help="Turn on blinking for all devices")
@click.pass_context
@connection_command()
@handle_service_errors(BlinkError)
def blink_all_on(ctx: Context) -> None:
    r"""Turn on blinking for all discovered devices.

    Args:
        ctx: Click context object.

    Examples:
        \b
        xp conbus blink all on
    """

    def on_finish(discovered_devices: ConbusBlinkResponse) -> None:
        """Handle successful completion of blink all on command.

        Args:
            discovered_devices: Blink response with all devices.
        """
        click.echo(json.dumps(discovered_devices.to_dict(), indent=2))

    def progress(message: str) -> None:
        """Handle progress updates during blink all on operation.

        Args:
            message: Progress message string.
        """
        click.echo(message)

    service: ConbusBlinkAllService = (
        ctx.obj.get("container").get_container().resolve(ConbusBlinkAllService)
    )
    with service:
        service.send_blink_all_telegram("on", progress, on_finish, 0.5)

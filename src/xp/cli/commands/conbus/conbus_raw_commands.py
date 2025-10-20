"""Conbus raw telegram CLI commands."""

import json

import click
from click import Context

from xp.cli.commands.conbus.conbus import conbus
from xp.cli.utils.decorators import (
    connection_command,
)
from xp.models.conbus.conbus_raw import ConbusRawResponse
from xp.services.conbus.conbus_raw_service import ConbusRawService


@conbus.command("raw")
@click.argument("raw_telegrams")
@click.pass_context
@connection_command()
def send_raw_telegrams(ctx: Context, raw_telegrams: str) -> None:
    r"""Send raw telegram sequence to Conbus server.

    Accepts a string containing one or more telegrams in format <...>.
    Multiple telegrams should be concatenated without separators.

    Args:
        ctx: Click context object.
        raw_telegrams: Raw telegram string(s).

    Examples:
        \b
        xp conbus raw '<S2113010000F02D12>'
        xp conbus raw '<S2113010000F02D12><S2113010001F02D12><S2113010002F02D12>'
        xp conbus raw '<S0012345003F02D12FM>...<S0012345009F02D12FF>'
    """
    service: ConbusRawService = (
        ctx.obj.get("container").get_container().resolve(ConbusRawService)
    )

    def on_progress(message: str) -> None:
        """Handle progress updates during raw telegram sending.

        Args:
            message: Progress message string.
        """
        click.echo(message)

    def on_finish(service_response: ConbusRawResponse) -> None:
        """Handle successful completion of raw telegram sending.

        Args:
            service_response: Raw response object.
        """
        click.echo(json.dumps(service_response.to_dict(), indent=2))

    with service:
        service.send_raw_telegram(
            raw_input=raw_telegrams,
            progress_callback=on_progress,
            finish_callback=on_finish,
            timeout_seconds=5.0,
        )

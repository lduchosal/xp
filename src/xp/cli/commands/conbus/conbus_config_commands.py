"""Conbus configuration CLI commands."""

import json

import click
from click import Context

from xp.cli.commands.conbus.conbus import conbus
from xp.cli.utils.decorators import handle_service_errors
from xp.models import ConbusClientConfig


@conbus.command("config")
@click.pass_context
@handle_service_errors(Exception)
def show_config(ctx: Context) -> None:
    r"""Display current Conbus client configuration.

    Args:
        ctx: Click context object.

    Examples:
        \b
        xp conbus config
    """
    config: ConbusClientConfig = (
        ctx.obj.get("container").get_container().resolve(ConbusClientConfig)
    )
    click.echo(json.dumps(config.conbus.model_dump(mode="json"), indent=2))

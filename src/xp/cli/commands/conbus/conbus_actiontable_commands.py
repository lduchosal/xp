"""ActionTable CLI commands."""

import json
from dataclasses import asdict

import click
from click import Context

from xp.cli.commands.conbus.conbus import conbus_actiontable
from xp.cli.utils.decorators import (
    connection_command,
    handle_service_errors,
)
from xp.cli.utils.serial_number_type import SERIAL
from xp.services.conbus.actiontable.actiontable_service import (
    ActionTableError,
    ActionTableService,
)


@conbus_actiontable.command("download", short_help="Download ActionTable")
@click.argument("serial_number", type=SERIAL)
@click.pass_context
@connection_command()
@handle_service_errors(ActionTableError)
def conbus_download_actiontable(ctx: Context, serial_number: str) -> None:
    """Download action table from XP module"""
    service = ctx.obj.get("container").get_container().resolve(ActionTableService)

    with service:
        actiontable = service.download_actiontable(serial_number)
        output = {
            "serial_number": serial_number,
            "actiontable": asdict(actiontable),
        }

        click.echo(json.dumps(output, indent=2, default=str))

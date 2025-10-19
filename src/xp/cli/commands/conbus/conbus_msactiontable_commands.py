"""XP24 Action Table CLI commands."""

import json
from dataclasses import asdict

import click
from click import Context

from xp.cli.commands.conbus.conbus import conbus_msactiontable
from xp.cli.utils.decorators import (
    connection_command,
)
from xp.cli.utils.serial_number_type import SERIAL
from xp.cli.utils.xp_module_type import XP_MODULE_TYPE
from xp.models.actiontable.actiontable import ActionTable
from xp.services.conbus.actiontable.msactiontable_service import (
    MsActionTableService,
)


@conbus_msactiontable.command("download", short_help="Download MSActionTable")
@click.argument("serial_number", type=SERIAL)
@click.argument("xpmoduletype", type=XP_MODULE_TYPE)
@click.pass_context
@connection_command()
def conbus_download_msactiontable(
    ctx: Context, serial_number: str, xpmoduletype: str
) -> None:
    """Download MS action table from XP24 module"""
    service = ctx.obj.get("container").get_container().resolve(MsActionTableService)

    def progress_callback(progress: str) -> None:
        click.echo(progress, nl=False)

    def finish_callback(action_table: ActionTable) -> None:
        output = {
            "serial_number": serial_number,
            "xpmoduletype": xpmoduletype,
            "action_table": asdict(action_table),
        }
        click.echo(json.dumps(output, indent=2, default=str))

    def error_callback(error: str) -> None:
        click.echo(f"Error: {error}")
        raise click.Abort()

    with service:
        service.start(
            serial_number=serial_number,
            xpmoduletype=xpmoduletype,
            progress_callback=progress_callback,
            finish_callback=finish_callback,
            error_callback=error_callback,
        )

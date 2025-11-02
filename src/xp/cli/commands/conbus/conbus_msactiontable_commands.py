"""XP24 Action Table CLI commands."""

import json
from dataclasses import asdict
from typing import Union

import click
from click import Context

from xp.cli.commands.conbus.conbus import conbus_msactiontable
from xp.cli.utils.decorators import (
    connection_command,
)
from xp.cli.utils.serial_number_type import SERIAL
from xp.cli.utils.xp_module_type import XP_MODULE_TYPE
from xp.models.actiontable.msactiontable_xp20 import Xp20MsActionTable
from xp.models.actiontable.msactiontable_xp24 import Xp24MsActionTable
from xp.models.actiontable.msactiontable_xp33 import Xp33MsActionTable
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
    """Download MS action table from XP24 module.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.
        xpmoduletype: XP module type.
    """
    service: MsActionTableService = (
        ctx.obj.get("container").get_container().resolve(MsActionTableService)
    )

    def progress_callback(progress: str) -> None:
        """Handle progress updates during MS action table download.

        Args:
            progress: Progress message string.
        """
        click.echo(progress, nl=False)

    def on_finish(
        action_table: Union[
            Xp20MsActionTable, Xp24MsActionTable, Xp33MsActionTable, None
        ],
    ) -> None:
        """Handle successful completion of MS action table download.

        Args:
            action_table: Downloaded MS action table object or None if failed.

        Raises:
            Abort: If action table download failed.
        """
        if action_table is None:
            click.echo("Error: Failed to download MS action table")
            raise click.Abort()

        output = {
            "serial_number": serial_number,
            "xpmoduletype": xpmoduletype,
            "action_table": asdict(action_table),
        }
        click.echo(json.dumps(output, indent=2, default=str))

    def error_callback(error: str) -> None:
        """Handle errors during MS action table download.

        Args:
            error: Error message string.

        Raises:
            Abort: Always raised to abort the command on error.
        """
        click.echo(f"Error: {error}")
        raise click.Abort()

    with service:
        service.start(
            serial_number=serial_number,
            xpmoduletype=xpmoduletype,
            progress_callback=progress_callback,
            finish_callback=on_finish,
            error_callback=error_callback,
        )

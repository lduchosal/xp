"""ActionTable CLI commands."""

import json
from dataclasses import asdict
from typing import Dict, Any

import click
from click import Context

from xp.cli.commands.conbus.conbus import conbus_actiontable
from xp.cli.utils.decorators import (
    connection_command,
)
from xp.cli.utils.serial_number_type import SERIAL
from xp.models.actiontable.actiontable import ActionTable
from xp.services.actiontable.actiontable_serializer import ActionTableSerializer
from xp.services.conbus.actiontable.actiontable_service import (
    ActionTableService,
)


@conbus_actiontable.command("download", short_help="Download ActionTable")
@click.argument("serial_number", type=SERIAL)
@click.pass_context
@connection_command()
def conbus_download_actiontable(ctx: Context, serial_number: str) -> None:
    """Download action table from XP module.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.
    """
    service: ActionTableService = (
        ctx.obj.get("container").get_container().resolve(ActionTableService)
    )

    def progress_callback(progress: str) -> None:
        """Handle progress updates during action table download.

        Args:
            progress: Progress message string.
        """
        click.echo(progress)

    def on_finish(actiontable: ActionTable, actiontable_dict: Dict[str, Any], actiontable_short: list[str]) -> None:
        """Handle successful completion of action table download.

        Args:
            actiontable: Downloaded action table object.
        """
        output = {
            "serial_number": serial_number,
            "actiontable_short": actiontable_short,
            "actiontable": actiontable_dict,
        }
        click.echo(json.dumps(output, indent=2, default=str))

    def error_callback(error: str) -> None:
        """Handle errors during action table download.

        Args:
            error: Error message string.
        """
        click.echo(error)

    with service:
        service.start(
            serial_number=serial_number,
            progress_callback=progress_callback,
            finish_callback=on_finish,
            error_callback=error_callback,
        )

"""ActionTable CLI commands."""

import json
from dataclasses import asdict

import click

from ..utils.decorators import (
    connection_command,
    handle_service_errors,
)
from ..utils.serial_number_type import SERIAL
from ...services.actiontable_service import (
    ActionTableService,
    ActionTableError,
)

from .conbus import conbus_actiontable


@conbus_actiontable.command("download", short_help="Download ActionTable")
@click.argument("serial_number", type=SERIAL)
@connection_command()
@handle_service_errors(ActionTableError)
def conbus_download_actiontable(serial_number: str) -> None:
    """Download action table from XP module"""
    service = ActionTableService()

    with service:
        actiontable = service.download_actiontable(serial_number)
        output = {
            "serial_number": serial_number,
            "actiontable": asdict(actiontable),
        }

        click.echo(json.dumps(output, indent=2, default=str))

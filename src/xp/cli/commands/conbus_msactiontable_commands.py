"""XP24 Action Table CLI commands."""

import json
from dataclasses import asdict

import click

from ..utils.decorators import (
    connection_command,
    handle_service_errors,
)
from ..utils.serial_number_type import SERIAL
from ...services.xp24_action_table_service import (
    Xp24ActionTableService,
    Xp24ActionTableError,
)

from .conbus import conbus_msactiontable


@conbus_msactiontable.command("download", short_help="Download MSActionTable")
@click.argument("serial_number", type=SERIAL)
@connection_command()
@handle_service_errors(Xp24ActionTableError)
def conbus_download_msactiontable(serial_number: str) -> None:
    """Download MS action table from XP24 module"""
    service = Xp24ActionTableService()

    with service:
        action_table = service.download_action_table(serial_number)
        output = {
            "serial_number": serial_number,
            "action_table": asdict(action_table),
            "raw": "PLACEHOLDER_RAW_DATA",  # TODO: Add raw data extraction
        }

        click.echo(json.dumps(output, indent=2, default=str))

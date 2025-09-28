"""XP24 Action Table CLI commands."""

import json
from dataclasses import asdict

import click

from ..utils.decorators import (
    connection_command,
    handle_service_errors,
)
from ..utils.serial_number_type import SERIAL
from ..utils.xp_module_type import XP_MODULE_TYPE
from ...services.msactiontable_service import (
    MsActionTableService,
    MsActionTableError,
)

from .conbus import conbus_msactiontable


@conbus_msactiontable.command("download", short_help="Download MSActionTable")
@click.argument("serial_number", type=SERIAL)
@click.argument("xpmoduletype", type=XP_MODULE_TYPE)
@connection_command()
@handle_service_errors(MsActionTableError)
def conbus_download_msactiontable(serial_number: str, xpmoduletype: str) -> None:
    """Download MS action table from XP24 module"""
    service = MsActionTableService()

    with service:
        action_table = service.download_action_table(serial_number, xpmoduletype)
        output = {
            "serial_number": serial_number,
            "xpmoduletype": xpmoduletype,
            "action_table": asdict(action_table),
        }

        click.echo(json.dumps(output, indent=2, default=str))

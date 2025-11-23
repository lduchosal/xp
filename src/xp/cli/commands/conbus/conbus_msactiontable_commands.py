"""XP24 Action Table CLI commands."""

import json
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
from xp.models.config.conson_module_config import ConsonModuleConfig
from xp.services.conbus.msactiontable.msactiontable_download_service import (
    MsActionTableDownloadService,
)
from xp.services.conbus.msactiontable.msactiontable_list_service import (
    MsActionTableListService,
)
from xp.services.conbus.msactiontable.msactiontable_show_service import (
    MsActionTableShowService,
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
    service: MsActionTableDownloadService = (
        ctx.obj.get("container").get_container().resolve(MsActionTableDownloadService)
    )

    def on_progress(progress: str) -> None:
        """Handle progress updates during MS action table download.

        Args:
            progress: Progress message string.
        """
        click.echo(progress, nl=False)

    def on_finish(
        msaction_table: Union[
            Xp20MsActionTable, Xp24MsActionTable, Xp33MsActionTable, None
        ],
        msaction_table_short: str
    ) -> None:
        """Handle successful completion of MS action table download.

        Args:
            msaction_table: Downloaded MS action table object or None if failed.
            msaction_table_short: Short version of MS action table object or None if failed.

        Raises:
            Abort: If action table download failed.
        """
        service.stop_reactor()
        if msaction_table is None:
            click.echo("Error: Failed to download MS action table")
            raise click.Abort()

        output = {
            "serial_number": serial_number,
            "xpmoduletype": xpmoduletype,
            "msaction_table_short": msaction_table_short,
            "msaction_table": msaction_table.model_dump(),
        }
        click.echo(json.dumps(output, indent=2, default=str))

    def on_error(error: str) -> None:
        """Handle errors during MS action table download.

        Args:
            error: Error message string.
        """
        click.echo(f"Error: {error}")

    with service:
        service.on_progress.connect(on_progress)
        service.on_error.connect(on_error)
        service.on_finish.connect(on_finish)
        service.start(
            serial_number=serial_number,
            xpmoduletype=xpmoduletype,
        )
        service.start_reactor()


@conbus_msactiontable.command("list", short_help="List modules with MsActionTable")
@click.pass_context
def conbus_list_msactiontable(ctx: Context) -> None:
    """List all modules with action table configurations from conson.yml.

    Args:
        ctx: Click context object.
    """
    service: MsActionTableListService = (
        ctx.obj.get("container").get_container().resolve(MsActionTableListService)
    )

    def on_finish(module_list: dict) -> None:
        """Handle successful completion of action table list.

        Args:
            module_list: Dictionary containing modules and total count.
        """
        click.echo(json.dumps(module_list, indent=2, default=str))

    def on_error(error: str) -> None:
        """Handle errors during action table list.

        Args:
            error: Error message string.
        """
        click.echo(error)

    with service:
        service.on_finish.connect(on_finish)
        service.on_error.connect(on_error)
        service.start()


@conbus_msactiontable.command("show", short_help="Show MsActionTable configuration")
@click.argument("serial_number", type=SERIAL)
@click.pass_context
def conbus_show_msactiontable(ctx: Context, serial_number: str) -> None:
    """Show ms action table configuration for a specific module from conson.yml.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.
    """
    service: MsActionTableShowService = (
        ctx.obj.get("container").get_container().resolve(MsActionTableShowService)
    )

    def on_finish(module: ConsonModuleConfig) -> None:
        """Handle successful completion of action table show.

        Args:
            module: Dictionary containing module configuration.
        """
        module_data = module.model_dump()
        module_data.pop("action_table", None)
        click.echo(json.dumps(module_data, indent=2, default=str))

    def error_callback(error: str) -> None:
        """Handle errors during action table show.

        Args:
            error: Error message string.
        """
        click.echo(error)

    with service:
        service.start(
            serial_number=serial_number,
            finish_callback=on_finish,
            error_callback=error_callback,
        )

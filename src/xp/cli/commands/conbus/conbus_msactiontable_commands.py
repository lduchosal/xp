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
        msaction_table_short: str,
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

        click.echo(f"\nModule: {serial_number}")
        click.echo("Short:")
        for line in msaction_table_short.split("\n"):
            click.echo(f"  - {line}")
        click.echo("")

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
        click.echo(f"\nModule: {module.alias} ({module.serial_number})")

        # Display short format if action table exists
        if module.xp33_msaction_table:
            click.echo("Short:")
            short_format = module.xp33_msaction_table.to_short_format()
            for line in short_format.split("\n"):
                click.echo(f"  - {line}")
        elif module.xp24_msaction_table:
            click.echo("Short:")
            short_format = module.xp24_msaction_table.to_short_format()
            for line in short_format.split("\n"):
                click.echo(f"  - {line}")
        elif module.xp20_msaction_table:
            click.echo("Short:")
            short_format = module.xp20_msaction_table.to_short_format()
            for line in short_format.split("\n"):
                click.echo(f"  - {line}")

        # Display full YAML format
        click.echo("Full:")
        module_data = module.model_dump()
        module_data.pop("action_table", None)

        # Show the action table in YAML format
        if module.xp33_msaction_table:
            yaml_dict = {"xp33_msaction_table": module.xp33_msaction_table.model_dump()}
            click.echo(_format_yaml(yaml_dict, indent=2))
        elif module.xp24_msaction_table:
            yaml_dict = {"xp24_msaction_table": module.xp24_msaction_table.model_dump()}
            click.echo(_format_yaml(yaml_dict, indent=2))
        elif module.xp20_msaction_table:
            yaml_dict = {"xp20_msaction_table": module.xp20_msaction_table.model_dump()}
            click.echo(_format_yaml(yaml_dict, indent=2))

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


def _format_yaml(data: dict, indent: int = 0) -> str:
    """Format a dictionary as YAML-like output.

    Args:
        data: Dictionary to format.
        indent: Current indentation level.

    Returns:
        YAML-like formatted string.
    """
    lines = []
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{' ' * indent}{key}:")
            lines.append(_format_yaml(value, indent + 2))
        elif isinstance(value, list):
            lines.append(f"{' ' * indent}{key}:")
            for item in value:
                if isinstance(item, dict):
                    lines.append(_format_yaml(item, indent + 2))
                else:
                    lines.append(f"{' ' * (indent + 2)}- {item}")
        else:
            lines.append(f"{' ' * indent}{key}: {value}")
    return "\n".join(lines)

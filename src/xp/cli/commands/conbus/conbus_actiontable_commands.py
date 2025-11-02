"""ActionTable CLI commands."""

import json
from contextlib import suppress
from pathlib import Path
from typing import Any

import click
from click import Context

from xp.cli.commands.conbus.conbus import conbus_actiontable
from xp.cli.utils.decorators import (
    connection_command,
)
from xp.cli.utils.serial_number_type import SERIAL
from xp.models.actiontable.actiontable import ActionTable
from xp.models.homekit.homekit_conson_config import (
    ConsonModuleConfig,
    ConsonModuleListConfig,
)
from xp.services.conbus.actiontable.actiontable_download_service import (
    ActionTableService,
)
from xp.services.conbus.actiontable.actiontable_list_service import (
    ActionTableListService,
)
from xp.services.conbus.actiontable.actiontable_show_service import (
    ActionTableShowService,
)
from xp.services.conbus.actiontable.actiontable_upload_service import (
    ActionTableUploadService,
)


class ActionTableError(Exception):
    """Raised when ActionTable operations fail."""

    pass


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

    def on_finish(
        _actiontable: ActionTable,
        actiontable_dict: dict[str, Any],
        actiontable_short: list[str],
    ) -> None:
        """Handle successful completion of action table download.

        Args:
            _actiontable: Downloaded action table object.
            actiontable_dict: Dictionary representation of action table.
            actiontable_short: List of textual format strings.
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


@conbus_actiontable.command("upload", short_help="Upload ActionTable")
@click.argument("serial_number", type=SERIAL)
@click.pass_context
@connection_command()
def conbus_upload_actiontable(ctx: Context, serial_number: str) -> None:
    """Upload action table from conson.yml to XP module.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.
    """
    service: ActionTableUploadService = (
        ctx.obj.get("container").get_container().resolve(ActionTableUploadService)
    )

    click.echo(f"Uploading action table to {serial_number}...")

    # Track number of entries for success message
    entries_count = 0

    def progress_callback(progress: str) -> None:
        """Handle progress updates during action table upload.

        Args:
            progress: Progress message string.
        """
        click.echo(progress, nl=False)

    def success_callback() -> None:
        """Handle successful completion of action table upload."""
        click.echo("\nAction table uploaded successfully")
        if entries_count > 0:
            click.echo(f"{entries_count} entries written")

    def error_callback(error: str) -> None:
        """Handle errors during action table upload.

        Args:
            error: Error message string.

        Raises:
            ActionTableError: Always raised with upload failure message.
        """
        raise ActionTableError(f"Upload failed: {error}")

    with service:
        # Load config to get entry count for success message
        config_path = Path.cwd() / "conson.yml"
        if config_path.exists():
            with suppress(Exception):
                config = ConsonModuleListConfig.from_yaml(str(config_path))
                module = config.find_module(serial_number)
                if module and module.action_table:
                    entries_count = len(module.action_table)

        service.start(
            serial_number=serial_number,
            progress_callback=progress_callback,
            success_callback=success_callback,
            error_callback=error_callback,
        )


@conbus_actiontable.command("list", short_help="List modules with ActionTable")
@click.pass_context
def conbus_list_actiontable(ctx: Context) -> None:
    """List all modules with action table configurations from conson.yml.

    Args:
        ctx: Click context object.
    """
    service: ActionTableListService = (
        ctx.obj.get("container").get_container().resolve(ActionTableListService)
    )

    def on_finish(module_list: dict) -> None:
        """Handle successful completion of action table list.

        Args:
            module_list: Dictionary containing modules and total count.
        """
        click.echo(json.dumps(module_list, indent=2, default=str))

    def error_callback(error: str) -> None:
        """Handle errors during action table list.

        Args:
            error: Error message string.
        """
        click.echo(error)

    with service:
        service.start(
            finish_callback=on_finish,
            error_callback=error_callback,
        )


@conbus_actiontable.command("show", short_help="Show ActionTable configuration")
@click.argument("serial_number", type=SERIAL)
@click.pass_context
def conbus_show_actiontable(ctx: Context, serial_number: str) -> None:
    """Show action table configuration for a specific module from conson.yml.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.
    """
    service: ActionTableShowService = (
        ctx.obj.get("container").get_container().resolve(ActionTableShowService)
    )

    def on_finish(module: ConsonModuleConfig) -> None:
        """Handle successful completion of action table show.

        Args:
            module: Dictionary containing module configuration.
        """
        click.echo(json.dumps(module.model_dump(), indent=2, default=str))

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

"""ActionTable CLI commands."""

import json
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
from xp.models.homekit.homekit_conson_config import ConsonModuleListConfig
from xp.services.actiontable.actiontable_serializer import ActionTableSerializer
from xp.services.conbus.actiontable.actiontable_service import ActionTableService
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

    Raises:
        ActionTableError: If conson.yml not found, module not found,
            no action_table configured, or invalid action table format.
    """
    # Load conson.yml configuration
    config_path = Path.cwd() / "conson.yml"
    if not config_path.exists():
        raise ActionTableError("conson.yml not found in current directory")

    config = ConsonModuleListConfig.from_yaml(str(config_path))
    module = config.find_module(serial_number)  # noqa: FURB184

    if not module:
        raise ActionTableError(f"Module {serial_number} not found in conson.yml")

    if not module.action_table:
        raise ActionTableError(f"No action_table configured for module {serial_number}")

    # Store action_table for later use
    action_table_strings = module.action_table

    # Parse action table strings to ActionTable object
    serializer = ActionTableSerializer()
    try:
        action_table = serializer.parse_action_table(action_table_strings)
    except ValueError as e:
        raise ActionTableError(f"Invalid action table format: {e}")

    service: ActionTableUploadService = (
        ctx.obj.get("container").get_container().resolve(ActionTableUploadService)
    )

    click.echo(f"Uploading action table to {serial_number}...")

    def progress_callback(progress: str) -> None:
        """Handle progress updates during action table upload.

        Args:
            progress: Progress message string.
        """
        click.echo(progress, nl=False)

    def success_callback() -> None:
        """Handle successful completion of action table upload."""
        click.echo("\nAction table uploaded successfully")
        click.echo(f"{len(action_table_strings)} entries written")

    def error_callback(error: str) -> None:
        """Handle errors during action table upload.

        Args:
            error: Error message string.

        Raises:
            ActionTableError: Always raised with upload failure message.
        """
        raise ActionTableError(f"Upload failed: {error}")

    with service:
        service.start(
            serial_number=serial_number,
            action_table=action_table,
            progress_callback=progress_callback,
            success_callback=success_callback,
            error_callback=error_callback,
        )

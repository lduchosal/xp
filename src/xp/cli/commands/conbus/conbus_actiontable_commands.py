"""ActionTable CLI commands."""

import json

import click
from click import Context

from xp.cli.commands.conbus.conbus import conbus_actiontable
from xp.cli.utils.decorators import (
    connection_command,
)
from xp.cli.utils.serial_number_type import SERIAL
from xp.models.actiontable.actiontable import ActionTable
from xp.models.actiontable.actiontable_type import ActionTableType, ActionTableType2
from xp.models.config.conson_module_config import (
    ConsonModuleConfig,
)
from xp.services.conbus.actiontable.actiontable_download_service import (
    ActionTableDownloadService,
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
    """
    Download action table from XP module.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.
    """
    service: ActionTableDownloadService = (
        ctx.obj.get("container").get_container().resolve(ActionTableDownloadService)
    )

    def on_progress(progress: str) -> None:
        """
        Handle progress updates during action table download.

        Args:
            progress: Progress message string.
        """
        click.echo(progress, nl=False)

    def on_actiontable_received(
        _actiontable: ActionTable,
        actiontable_short: list[str],
    ) -> None:
        """
        Handle successful completion of action table download.

        Args:
            _actiontable: a list of ActionTableEntries.
            actiontable_short: short representation of action table.
        """
        output = {
            "serial_number": serial_number,
            "actiontable_short": actiontable_short,
        }
        click.echo(json.dumps(output, indent=2, default=str))

    def on_finish() -> None:
        """Handle successful completion of action table download."""
        service.stop_reactor()

    def on_error(error: str) -> None:
        """
        Handle errors during action table download.

        Args:
            error: Error message string.
        """
        click.echo(error)
        service.stop_reactor()

    with service:
        service.on_progress.connect(on_progress)
        service.on_finish.connect(on_finish)
        service.on_actiontable_received.connect(on_actiontable_received)
        service.on_error.connect(on_error)
        service.configure(
            serial_number=serial_number,
            actiontable_type=ActionTableType.ACTIONTABLE,
        )
        service.start_reactor()


@conbus_actiontable.command("upload", short_help="Upload ActionTable")
@click.argument("serial_number", type=SERIAL)
@click.pass_context
@connection_command()
def conbus_upload_actiontable(ctx: Context, serial_number: str) -> None:
    """
    Upload action table from conson.yml to XP module.

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
        """
        Handle progress updates during action table upload.

        Args:
            progress: Progress message string.
        """
        click.echo(progress, nl=False)

    def on_finish(success: bool) -> None:
        """
        Handle completion of action table upload.

        Args:
            success: True if upload succeeded.
        """
        if success:
            click.echo("\nAction table uploaded successfully")
            if entries_count > 0:
                click.echo(f"{entries_count} entries written")
        service.stop_reactor()

    def on_error(error: str) -> None:
        """
        Handle errors during action table upload.

        Args:
            error: Error message string.

        Raises:
            ActionTableError: Always raised with upload failure message.
        """
        service.stop_reactor()
        raise ActionTableError(f"Upload failed: {error}")

    with service:
        # Load config to get entry count for success message
        service.on_progress.connect(progress_callback)
        service.on_finish.connect(on_finish)
        service.on_error.connect(on_error)
        service.start(
            serial_number=serial_number, actiontable_type=ActionTableType2.ACTIONTABLE
        )
        service.start_reactor()


@conbus_actiontable.command("list", short_help="List modules with ActionTable")
@click.pass_context
def conbus_list_actiontable(ctx: Context) -> None:
    """
    List all modules with action table configurations from conson.yml.

    Args:
        ctx: Click context object.
    """
    service: ActionTableListService = (
        ctx.obj.get("container").get_container().resolve(ActionTableListService)
    )

    def on_finish(module_list: dict) -> None:
        """
        Handle successful completion of action table list.

        Args:
            module_list: Dictionary containing modules and total count.
        """
        click.echo(json.dumps(module_list, indent=2, default=str))

    def on_error(error: str) -> None:
        """
        Handle errors during action table list.

        Args:
            error: Error message string.
        """
        click.echo(error)

    with service:
        service.on_finish.connect(on_finish)
        service.on_error.connect(on_error)
        service.start()


@conbus_actiontable.command("show", short_help="Show ActionTable configuration")
@click.argument("serial_number", type=SERIAL)
@click.pass_context
def conbus_show_actiontable(ctx: Context, serial_number: str) -> None:
    """
    Show action table configuration for a specific module from conson.yml.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.
    """
    service: ActionTableShowService = (
        ctx.obj.get("container").get_container().resolve(ActionTableShowService)
    )

    def on_finish(module: ConsonModuleConfig) -> None:
        """
        Handle successful completion of action table show.

        Args:
            module: Dictionary containing module configuration.
        """
        module_data = module.model_dump()
        module_data.pop("msactiontable", None)
        click.echo(json.dumps(module_data, indent=2, default=str))

    def error_callback(error: str) -> None:
        """
        Handle errors during action table show.

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

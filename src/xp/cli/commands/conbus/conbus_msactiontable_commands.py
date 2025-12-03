"""XP24 Action Table CLI commands."""

import json
from typing import Any, Optional, Union

import click
from click import Context

from xp.cli.commands.conbus.conbus import conbus_msactiontable
from xp.cli.utils.decorators import (
    connection_command,
)
from xp.cli.utils.serial_number_type import SERIAL
from xp.models.actiontable.actiontable_type import ActionTableType, ActionTableType2
from xp.models.config.conson_module_config import ConsonModuleConfig
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


class XpModuleTypeChoice(click.ParamType):
    """
    Click parameter type for validating XP module types.

    Attributes:
        name: The parameter type name.
        choices: List of valid module type strings.
    """

    name = "xpmoduletype"

    def __init__(self) -> None:
        """Initialize the XpModuleTypeChoice parameter type."""
        self.choices = ["xp20", "xp24", "xp31", "xp33"]

    def convert(
        self,
        value: Any,
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> Any:
        """
        Convert and validate XP module type input.

        Args:
            value: The input value to convert.
            param: The Click parameter.
            ctx: The Click context.

        Returns:
            Lowercase module type string if valid, None if input is None.
        """
        if value is None:
            return value
        normalized_value = value.lower()
        if normalized_value in self.choices:
            return normalized_value
        choices_list = "\n".join(f" - {choice}" for choice in sorted(self.choices))
        self.fail(
            f"{value!r} is not a valid choice. Choose from:\n{choices_list}",
            param,
            ctx,
        )


XP_MODULE_TYPE = XpModuleTypeChoice()


def _get_actiontable_type(xpmoduletype: str) -> ActionTableType:
    """
    Map xpmoduletype string to ActionTableType enum.

    Args:
        xpmoduletype: XP module type string (xp20, xp24, xp33).

    Returns:
        Corresponding ActionTableType enum value.

    Raises:
        ClickException: If module type is not supported.
    """
    type_map = {
        "xp20": ActionTableType.MSACTIONTABLE_XP20,
        "xp24": ActionTableType.MSACTIONTABLE_XP24,
        "xp33": ActionTableType.MSACTIONTABLE_XP33,
    }
    if xpmoduletype not in type_map:
        raise click.ClickException(f"Unsupported module type: {xpmoduletype}")
    return type_map[xpmoduletype]


@conbus_msactiontable.command("download", short_help="Download MSActionTable")
@click.argument("serial_number", type=SERIAL)
@click.argument("xpmoduletype", type=XP_MODULE_TYPE)
@click.pass_context
@connection_command()
def conbus_download_msactiontable(
    ctx: Context, serial_number: str, xpmoduletype: str
) -> None:
    """
    Download MS action table from XP24 module.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.
        xpmoduletype: XP module type.
    """
    service: ActionTableDownloadService = (
        ctx.obj.get("container").get_container().resolve(ActionTableDownloadService)
    )

    def on_progress(progress: str) -> None:
        """
        Handle progress updates during MS action table download.

        Args:
            progress: Progress message string.
        """
        click.echo(progress, nl=False)

    def on_actiontable_received(
        msaction_table: Any,
        msaction_table_short: list[str],
    ) -> None:
        """
        Handle successful completion of XP24 MS action table download.

        Args:
            msaction_table: Downloaded XP MS action table object.
            msaction_table_short: Short version of XP24 MS action table.
        """
        # Format short representation based on module type
        short_field_name = f"{xpmoduletype}_msaction_table"
        # XP24 returns single-element list, XP20/XP33 return multi-line lists
        short_value: Union[str, list[str]]
        if len(msaction_table_short) == 1:
            short_value = msaction_table_short[0]
        else:
            short_value = msaction_table_short

        output = {
            "serial_number": serial_number,
            "xpmoduletype": xpmoduletype,
            short_field_name: short_value,
            "msaction_table": msaction_table.model_dump(),
        }
        click.echo(json.dumps(output, indent=2, default=str))

    def on_finish() -> None:
        """Handle download completion."""
        service.stop_reactor()

    def on_error(error: str) -> None:
        """
        Handle errors during MS action table download.

        Args:
            error: Error message string.
        """
        click.echo(f"Error: {error}")
        service.stop_reactor()

    with service:
        service.on_progress.connect(on_progress)
        service.on_actiontable_received.connect(on_actiontable_received)
        service.on_finish.connect(on_finish)
        service.on_error.connect(on_error)
        service.configure(
            serial_number=serial_number,
            actiontable_type=_get_actiontable_type(xpmoduletype),
        )
        service.start_reactor()


@conbus_msactiontable.command("list", short_help="List modules with MsActionTable")
@click.pass_context
def conbus_list_msactiontable(ctx: Context) -> None:
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


@conbus_msactiontable.command("show", short_help="Show MsActionTable configuration")
@click.argument("serial_number", type=SERIAL)
@click.pass_context
def conbus_show_msactiontable(ctx: Context, serial_number: str) -> None:
    """
    Show ms action table configuration for a specific module from conson.yml.

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
        click.echo(f"\nModule: {module.name} ({module.serial_number})")

        # Display short format if action table exists
        if module.xp33_msaction_table:
            click.echo("Short:")
            for line in module.xp33_msaction_table:
                click.echo(f"  - {line}")
        elif module.xp24_msaction_table:
            click.echo("Short:")
            for line in module.xp24_msaction_table:
                click.echo(f"  - {line}")
        elif module.xp20_msaction_table:
            click.echo("Short:")
            for line in module.xp20_msaction_table:
                click.echo(f"  - {line}")

        # Display full YAML format
        click.echo("Full:")
        module_data = module.model_dump()
        module_data.pop("action_table", None)

        # Show the action table in YAML format
        if module.xp33_msaction_table:
            yaml_dict = {"xp33_msaction_table": module_data}
            click.echo(_format_yaml(yaml_dict, indent=2))
        elif module.xp24_msaction_table:
            yaml_dict = {"xp24_msaction_table": module_data}
            click.echo(_format_yaml(yaml_dict, indent=2))
        elif module.xp20_msaction_table:
            yaml_dict = {"xp20_msaction_table": module_data}
            click.echo(_format_yaml(yaml_dict, indent=2))

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


@conbus_msactiontable.command("upload", short_help="Upload MSActionTable")
@click.argument("serial_number", type=SERIAL)
@click.pass_context
@connection_command()
def conbus_upload_msactiontable(ctx: Context, serial_number: str) -> None:
    """
    Upload MS action table from conson.yml to XP module.

    Args:
        ctx: Click context object.
        serial_number: 10-digit module serial number.
    """
    service: ActionTableUploadService = (
        ctx.obj.get("container").get_container().resolve(ActionTableUploadService)
    )

    def on_progress(progress: str) -> None:
        """
        Handle progress updates during MS action table upload.

        Args:
            progress: Progress message string.
        """
        click.echo(progress, nl=False)

    def on_finish(success: bool) -> None:
        """
        Handle successful completion of MS action table upload.

        Args:
            success: Whether upload was successful.
        """
        service.stop_reactor()
        if success:
            click.echo("\nMsactiontable uploaded successfully")

    def on_error(error: str) -> None:
        """
        Handle errors during MS action table upload.

        Args:
            error: Error message string.
        """
        service.stop_reactor()
        click.echo(f"\nError: {error}")

    click.echo(f"Uploading msactiontable to {serial_number}...")

    with service:
        service.on_progress.connect(on_progress)
        service.on_error.connect(on_error)
        service.on_finish.connect(on_finish)
        service.start(
            serial_number=serial_number,
            actiontable_type=ActionTableType2.MSACTIONTABLE,
        )
        service.start_reactor()


def _format_yaml(data: dict, indent: int = 0) -> str:
    """
    Format a dictionary as YAML-like output.

    Args:
        data: Dictionary to format.
        indent: Current indentation level.

    Returns:
        YAML-like formatted string.
    """
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, dict):
            lines.extend((f"{' ' * indent}{key}:", _format_yaml(value, indent + 2)))
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

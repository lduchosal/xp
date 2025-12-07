"""Conbus export CLI commands."""

from contextlib import suppress

import click

from xp.cli.commands.conbus.conbus import conbus_export
from xp.cli.utils.decorators import connection_command
from xp.models.actiontable.actiontable_type import ActionTableType
from xp.models.conbus.conbus_export import ConbusExportResponse
from xp.models.config.conson_module_config import ConsonModuleConfig
from xp.services.conbus.conbus_export_actiontable_service import (
    ConbusActiontableExportService,
)
from xp.services.conbus.conbus_export_service import ConbusExportService


@conbus_export.command("config")
@click.pass_context
@connection_command()
def export_conbus_config(ctx: click.Context) -> None:
    r"""
    Export Conbus device metadata to YAML file.

    Discovers all devices on the Conbus network and queries their configuration
    datapoints to generate a complete export.yml file in conson.yml format.

    Args:
        ctx: Click context object.

    Examples:
        \b
        # Export device metadata to export.yml
        xp conbus export
        xp conbus export config
    """

    def on_progress(serial_number: str, current: int, total: int) -> None:
        """
        Handle progress updates during export.

        Args:
            serial_number: Serial number of discovered device.
            current: Current device number.
            total: Total devices discovered.
        """
        click.echo(f"Querying device {current}/{total}: {serial_number}...")

    def on_device_exported(module: ConsonModuleConfig) -> None:
        """
        Handle device export completion.

        Args:
            module: Exported module configuration.
        """
        module_type = module.module_type or "UNKNOWN"
        module_code = (
            module.module_type_code if module.module_type_code is not None else "?"
        )
        click.echo(f"  ✓ Module type: {module_type} ({module_code})")

        if module.link_number is not None:
            click.echo(f"  ✓ Link number: {module.link_number}")
        if module.sw_version:
            click.echo(f"  ✓ Software version: {module.sw_version}")

    def on_finish(result: ConbusExportResponse) -> None:
        """
        Handle export completion.

        Args:
            result: Export result.

        Raises:
            ClickException: When export fails with error message from result.
        """
        # Try to stop reactor (may already be stopped)
        with suppress(Exception):
            service.stop_reactor()

        if result.success:
            click.echo(
                f"\nExport complete: {result.output_file} ({result.device_count} devices)"
            )
        else:
            click.echo(f"Error: {result.error}", err=True)
            raise click.ClickException(result.error or "Export failed")

    service: ConbusExportService = (
        ctx.obj.get("container").get_container().resolve(ConbusExportService)
    )
    with service:
        service.on_progress.connect(on_progress)
        service.on_device_exported.connect(on_device_exported)
        service.on_finish.connect(on_finish)
        service.set_timeout(5)
        service.start_reactor()


@conbus_export.command("actiontable")
@click.pass_context
@connection_command()
def export_conbus_actiontable(ctx: click.Context) -> None:
    r"""
    Export Conbus device actiontable to YAML file.

    Read device list from conson.yml
    Export export.yml file in conson.yml format.

    Args:
        ctx: Click context object.

    Examples:
        \b
        # Export device metadata to export.yml
        xp conbus export
        xp conbus export actiontable
    """

    def on_progress(
        serial_number: str, actiontable_type: str, current: int, total: int
    ) -> None:
        """
        Handle progress updates during export.

        Args:
            serial_number: Serial number of discovered device.
            actiontable_type: Type of action table being exported.
            current: Current device number.
            total: Total devices discovered.
        """
        click.echo(
            f"Querying device {current}/{total}: {serial_number} / {actiontable_type}."
        )

    def on_device_actiontable_exported(
        module: ConsonModuleConfig,
        actiontable_type: ActionTableType,
        actiontable_short: str,
    ) -> None:
        """
        Handle device export completion.

        Args:
            module: Exported module configuration.
            actiontable_type: Type of action table exported.
            actiontable_short: Short representation of the action table.
        """
        serial_number = module.serial_number or "UNKNOWN"
        click.echo(f"  ✓ Module: {serial_number})")
        click.echo(f"  ✓ Action type: {actiontable_type}")
        click.echo(f"  ✓ Action table: {actiontable_short}")

    def on_finish(result: ConbusExportResponse) -> None:
        """
        Handle export completion.

        Args:
            result: Export result.

        Raises:
            ClickException: When export fails with error message from result.
        """
        # Try to stop reactor (may already be stopped)
        with suppress(Exception):
            service.stop_reactor()

        if result.success:
            click.echo(
                f"\nExport complete: {result.output_file} ({result.device_count} devices)"
            )
        else:
            click.echo(f"Error: {result.error}", err=True)
            raise click.ClickException(result.error or "Export failed")

    service: ConbusActiontableExportService = (
        ctx.obj.get("container").get_container().resolve(ConbusActiontableExportService)
    )
    with service:
        service.on_progress.connect(on_progress)
        service.on_device_actiontable_exported.connect(on_device_actiontable_exported)
        service.on_finish.connect(on_finish)
        service.set_timeout(5)
        service.configure()
        service.start_reactor()

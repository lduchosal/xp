"""Conbus export CLI command."""

from contextlib import suppress

import click

from xp.cli.commands.conbus.conbus import conbus
from xp.cli.utils.decorators import connection_command
from xp.models.conbus.conbus_export import ConbusExportResponse
from xp.models.homekit.homekit_conson_config import ConsonModuleConfig
from xp.services.conbus.conbus_export_service import ConbusExportService


@conbus.command("export")
@click.pass_context
@connection_command()
def export_conbus_config(ctx: click.Context) -> None:
    r"""Export Conbus device configuration to YAML file.

    Discovers all devices on the Conbus network and queries their configuration
    datapoints to generate a complete export.yml file in conson.yml format.

    Args:
        ctx: Click context object.

    Examples:
        \b
        # Export to export.yml in current directory
        xp conbus export
    """

    def on_progress(serial_number: str, current: int, total: int) -> None:
        """Handle progress updates during export.

        Args:
            serial_number: Serial number of discovered device.
            current: Current device number.
            total: Total devices discovered.
        """
        click.echo(f"Querying device {current}/{total}: {serial_number}...")

    def on_device_exported(module: ConsonModuleConfig) -> None:
        """Handle device export completion.

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
        """Handle export completion.

        Args:
            result: Export result.
        """
        # Try to stop reactor (may already be stopped)
        with suppress(Exception):
            service.stop_reactor()

        if result.export_status == "OK":
            click.echo(
                f"\nExport complete: {result.output_file} ({result.device_count} devices)"
            )
            ctx.exit(0)
        elif result.export_status == "FAILED_NO_DEVICES":
            click.echo("Error: No devices found on network", err=True)
            ctx.exit(1)
        elif result.export_status == "FAILED_TIMEOUT":
            click.echo(
                f"\nWarning: Partial export due to timeout: {result.output_file} ({result.device_count} devices)",
                err=True,
            )
            click.echo("Some devices may have incomplete configuration", err=True)
            ctx.exit(1)
        elif result.export_status == "FAILED_WRITE":
            click.echo(f"Error: Failed to write export file: {result.error}", err=True)
            ctx.exit(1)
        elif result.export_status == "FAILED_CONNECTION":
            click.echo(f"Error: Connection failed: {result.error}", err=True)
            ctx.exit(1)
        else:
            click.echo(f"Error: Export failed: {result.error}", err=True)
            ctx.exit(1)

    service: ConbusExportService = (
        ctx.obj.get("container").get_container().resolve(ConbusExportService)
    )
    with service:
        service.on_progress.connect(on_progress)
        service.on_device_exported.connect(on_device_exported)
        service.on_finish.connect(on_finish)
        service.set_timeout(5)
        service.start_reactor()

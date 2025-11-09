"""Conbus event operations CLI commands."""

import json

import click

from xp.cli.commands.conbus.conbus import conbus
from xp.cli.utils.decorators import connection_command
from xp.models import ConbusEventRawResponse
from xp.models.telegram.module_type_code import ModuleTypeCode
from xp.services.conbus.conbus_event_raw_service import ConbusEventRawService


@click.group(name="event")
def conbus_event() -> None:
    """Send event telegrams to Conbus modules."""
    pass


@conbus_event.command("raw")
@click.argument("module_type", type=str)
@click.argument("link_number", type=int)
@click.argument("input_number", type=int)
@click.argument("time_ms", type=int, default=1000)
@click.pass_context
@connection_command()
def send_event_raw(
    ctx: click.Context,
    module_type: str,
    link_number: int,
    input_number: int,
    time_ms: int,
) -> None:
    r"""Send raw event telegrams to simulate button presses.

    Args:
        ctx: Click context object.
        module_type: Module type code (e.g., CP20, XP33).
        link_number: Link number (0-99).
        input_number: Input number (0-9).
        time_ms: Delay between MAKE/BREAK events in milliseconds (default: 1000).

    Examples:
        \b
        xp conbus event raw CP20 00 00
        xp conbus event raw XP33 00 00 500
    """
    # Validate parameters
    if link_number < 0 or link_number > 99:
        click.echo(
            json.dumps({"error": "Link number must be between 0 and 99"}, indent=2)
        )
        return

    if input_number < 0 or input_number > 9:
        click.echo(
            json.dumps({"error": "Input number must be between 0 and 9"}, indent=2)
        )
        return

    if time_ms <= 0:
        click.echo(json.dumps({"error": "Time must be greater than 0"}, indent=2))
        return

    # Resolve module type to numeric code
    module_type_code: int = 0
    try:
        # Try to get the enum value by name
        module_type_enum = ModuleTypeCode[module_type.upper()]
        module_type_code = module_type_enum.value
    except KeyError:
        # Module type not found
        click.echo(
            json.dumps(
                {
                    "error": f"Unknown module type: {module_type}. Use module types like CP20, XP33, XP24, etc."
                },
                indent=2,
            )
        )
        return

    def on_finish(response: ConbusEventRawResponse) -> None:
        """Handle successful completion of event raw operation.

        Args:
            response: Event raw response with sent and received telegrams.
        """
        click.echo(json.dumps(response.to_dict(), indent=2))

    def on_progress(telegram: str) -> None:
        """Handle progress updates during event operation.

        Args:
            telegram: Received telegram.
        """
        click.echo(json.dumps({"telegram": telegram}))

    service: ConbusEventRawService = (
        ctx.obj.get("container").get_container().resolve(ConbusEventRawService)
    )
    service.run(
        module_type_code=module_type_code,
        link_number=link_number,
        input_number=input_number,
        time_ms=time_ms,
        progress_callback=on_progress,
        finish_callback=on_finish,
        timeout_seconds=5,
    )
    service.start_reactor()


# Register the event command group with conbus
conbus.add_command(conbus_event)

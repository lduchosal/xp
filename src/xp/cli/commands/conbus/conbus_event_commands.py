"""Conbus event operations CLI commands."""

import json

import click

from xp.cli.commands.conbus.conbus import conbus
from xp.cli.utils.decorators import connection_command
from xp.cli.utils.module_type_choice import MODULE_TYPE
from xp.models import ConbusEventRawResponse
from xp.services.conbus.conbus_event_list_service import ConbusEventListService
from xp.services.conbus.conbus_event_raw_service import ConbusEventRawService


@click.group(name="event")
def conbus_event() -> None:
    """Send event telegrams to Conbus modules."""
    pass


@conbus_event.command("list")
@click.pass_context
def list_events(ctx: click.Context) -> None:
    r"""List configured event telegrams from module action tables.

    Reads conson.yml configuration, parses action tables, and groups
    modules by their event keys to show which modules are assigned to
    each event (button configuration).

    Output is sorted by module count (most frequently used events first).

    Args:
        ctx: Click context object.

    Examples:
        \b
        xp conbus event list
    """
    service: ConbusEventListService = (
        ctx.obj.get("container").get_container().resolve(ConbusEventListService)
    )
    click.echo(json.dumps(service.list_events().to_dict(), indent=2))


@conbus_event.command("raw")
@click.argument("module_type", type=MODULE_TYPE)
@click.argument("link_number", type=click.IntRange(0, 99))
@click.argument("input_number", type=click.IntRange(0, 9))
@click.argument("time_ms", type=click.IntRange(min=1), default=1000)
@click.pass_context
@connection_command()
def send_event_raw(
    ctx: click.Context,
    module_type: int,
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
        module_type_code=module_type,
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

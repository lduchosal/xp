"""Term protocol CLI command for TUI monitoring."""

import click
from click import Context

from xp.cli.commands.term.term import term


@term.command("protocol")
@click.pass_context
def protocol_monitor(ctx: Context) -> None:
    r"""
    Start TUI for real-time protocol monitoring.

    Displays live RX/TX telegram stream from Conbus server
    in an interactive terminal interface.

    Args:
        ctx: Click context object.

    Examples:
        \b
        xp term protocol
    """
    from xp.term.protocol import ProtocolMonitorApp

    # Resolve ProtocolMonitorApp from container and run
    ctx.obj.get("container").get_container().resolve(ProtocolMonitorApp).run()


@term.command("state")
@click.pass_context
def state_monitor(ctx: Context) -> None:
    r"""
    Start TUI for module state monitoring.

    Displays module states from Conson configuration with real-time
    updates in an interactive terminal interface.

    Args:
        ctx: Click context object.

    Examples:
        \b
        xp term state
    """
    from xp.term.state import StateMonitorApp

    # Resolve StateMonitorApp from container and run
    ctx.obj.get("container").get_container().resolve(StateMonitorApp).run()


@term.command("homekit")
@click.pass_context
def homekit_monitor(ctx: Context) -> None:
    r"""
    Start TUI for HomeKit accessory monitoring.

    Displays HomeKit rooms and accessories with real-time state updates
    in an interactive terminal interface. Press action keys (a-z0-9) to
    toggle accessories.

    Args:
        ctx: Click context object.

    Examples:
        \b
        xp term homekit
    """
    from xp.term.homekit import HomekitApp

    # Resolve HomekitApp from container and run
    ctx.obj.get("container").get_container().resolve(HomekitApp).run()

"""Term protocol CLI command for TUI monitoring."""

import signal
from typing import Optional

import click
from click import Context

from xp.cli.commands.term.term import term
from xp.cli.utils.pid_file import remove_pid_file, write_pid_file


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

    app = ctx.obj.get("container").get_container().resolve(ProtocolMonitorApp)
    pid_file: Optional[str] = ctx.obj.get("pid_file")

    if pid_file:
        write_pid_file(pid_file)

    def signal_handler(signum: int, frame: object) -> None:
        app.exit()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        app.run()
    finally:
        if pid_file:
            remove_pid_file(pid_file)


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

    app = ctx.obj.get("container").get_container().resolve(StateMonitorApp)
    pid_file: Optional[str] = ctx.obj.get("pid_file")

    if pid_file:
        write_pid_file(pid_file)

    def signal_handler(signum: int, frame: object) -> None:
        app.exit()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        app.run()
    finally:
        if pid_file:
            remove_pid_file(pid_file)


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

    app = ctx.obj.get("container").get_container().resolve(HomekitApp)
    pid_file: Optional[str] = ctx.obj.get("pid_file")

    if pid_file:
        write_pid_file(pid_file)

    def signal_handler(signum: int, frame: object) -> None:
        app.exit()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        app.run()
    finally:
        if pid_file:
            remove_pid_file(pid_file)

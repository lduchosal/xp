"""Term protocol CLI command for TUI monitoring."""

import click
from click import Context

from xp.cli.commands.term.term import term


@term.command("protocol")
@click.pass_context
def protocol_monitor(ctx: Context) -> None:
    r"""Start TUI for real-time protocol monitoring.

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

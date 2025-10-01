"""Conbus CLI commands package."""

from xp.cli.commands.conbus.conbus import (
    conbus,
    conbus_actiontable,
    conbus_autoreport,
    conbus_blink,
    conbus_datapoint,
    conbus_lightlevel,
    conbus_linknumber,
    conbus_msactiontable,
    conbus_output,
)

# Import command modules to make them patchable in tests (Python 3.10 compatibility)
from xp.cli.commands.conbus import (
    conbus_actiontable_commands,
    conbus_msactiontable_commands,
)

__all__ = [
    "conbus",
    "conbus_blink",
    "conbus_output",
    "conbus_datapoint",
    "conbus_linknumber",
    "conbus_autoreport",
    "conbus_lightlevel",
    "conbus_msactiontable",
    "conbus_actiontable",
]

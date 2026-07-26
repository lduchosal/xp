# Copyright (c) 2025 ldvchosal
"""ActionTable type enumeration."""

from enum import Enum, StrEnum


# NOTE: not converted to StrEnum (UP042): members are interpolated in f-strings
# in src/xp/cli/commands/conbus/conbus_export_commands.py (CLI output would
# change from "ActionTableType.X" to the raw value).
class ActionTableType(str, Enum):  # noqa: UP042
    """ActionTable types for download/upload operations.

    Attributes:
        ACTIONTABLE: Standard action table.
        MSACTIONTABLE_XP20: Master station action table (XP20 format).
        MSACTIONTABLE_XP24: Master station action table (XP24 format).
        MSACTIONTABLE_XP33: Master station action table (XP33 format).

    """

    ACTIONTABLE = "actiontable"
    MSACTIONTABLE_XP20 = "msactiontable_xp20"
    MSACTIONTABLE_XP24 = "msactiontable_xp24"
    MSACTIONTABLE_XP33 = "msactiontable_xp33"


class ActionTableType2(StrEnum):
    """ActionTable types for download/upload operations.

    Attributes:
        ACTIONTABLE: Standard action table.
        MSACTIONTABLE: MS action table.

    """

    ACTIONTABLE = "actiontable"
    MSACTIONTABLE = "msactiontable"

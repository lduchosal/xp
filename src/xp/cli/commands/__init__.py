"""Command modules for XP CLI."""

# Main command groups

# Import conbus command groups (but not 'conbus' itself to avoid module shadowing in Python 3.10)
from xp.cli.commands.conbus.conbus import (
    conbus_actiontable,
    conbus_autoreport,
    conbus_blink,
    conbus_datapoint,
    conbus_lightlevel,
    conbus_linknumber,
    conbus_modulenumber,
    conbus_msactiontable,
    conbus_output,
)
from xp.cli.commands.conbus.conbus_actiontable_commands import (
    conbus_download_actiontable,
)

# Individual command functions that attach to groups
from xp.cli.commands.conbus.conbus_autoreport_commands import (
    get_autoreport_command,
    set_autoreport_command,
)
from xp.cli.commands.conbus.conbus_blink_commands import (
    blink_all_off,
    blink_all_on,
    conbus_blink_all,
    send_blink_off_telegram,
    send_blink_on_telegram,
)
from xp.cli.commands.conbus.conbus_config_commands import show_config
from xp.cli.commands.conbus.conbus_custom_commands import send_custom_telegram
from xp.cli.commands.conbus.conbus_datapoint_commands import (
    query_all_datapoints,
    query_datapoint,
)
from xp.cli.commands.conbus.conbus_discover_commands import send_discover_telegram
from xp.cli.commands.conbus.conbus_event_commands import conbus_event, send_event_raw
from xp.cli.commands.conbus.conbus_lightlevel_commands import (
    xp_lightlevel_get,
    xp_lightlevel_off,
    xp_lightlevel_on,
    xp_lightlevel_set,
)
from xp.cli.commands.conbus.conbus_linknumber_commands import (
    get_linknumber_command,
    set_linknumber_command,
)
from xp.cli.commands.conbus.conbus_modulenumber_commands import (
    get_modulenumber_command,
    set_modulenumber_command,
)
from xp.cli.commands.conbus.conbus_msactiontable_commands import (
    conbus_download_msactiontable,
)
from xp.cli.commands.conbus.conbus_output_commands import (
    xp_module_state,
    xp_output_off,
    xp_output_on,
    xp_output_status,
)
from xp.cli.commands.conbus.conbus_raw_commands import send_raw_telegrams
from xp.cli.commands.conbus.conbus_receive_commands import receive_telegrams
from xp.cli.commands.conbus.conbus_scan_commands import scan_module
from xp.cli.commands.file_commands import file
from xp.cli.commands.homekit.homekit import homekit
from xp.cli.commands.homekit.homekit_start_commands import homekit_start
from xp.cli.commands.module_commands import module
from xp.cli.commands.reverse_proxy_commands import reverse_proxy
from xp.cli.commands.server.server_commands import server
from xp.cli.commands.telegram.telegram import blink, checksum, linknumber, telegram
from xp.cli.commands.telegram.telegram_blink_commands import blink_off, blink_on
from xp.cli.commands.telegram.telegram_checksum_commands import (
    calculate_checksum,
    validate_checksum,
)
from xp.cli.commands.telegram.telegram_discover_commands import generate_discover
from xp.cli.commands.telegram.telegram_linknumber_commands import (
    generate_read_link_number,
    generate_set_link_number,
)
from xp.cli.commands.telegram.telegram_parse_commands import (
    parse_any_telegram,
    validate_telegram,
)
from xp.cli.commands.telegram.telegram_version_commands import generate_version_request
from xp.cli.commands.term.term import term
from xp.cli.commands.term.term_commands import protocol_monitor

__all__ = [
    # Main command groups (conbus excluded to avoid module shadowing)
    "conbus_blink",
    "conbus_output",
    "conbus_datapoint",
    "conbus_linknumber",
    "conbus_modulenumber",
    "conbus_autoreport",
    "conbus_lightlevel",
    "conbus_msactiontable",
    "conbus_actiontable",
    "conbus_event",
    "file",
    "module",
    "reverse_proxy",
    "server",
    "telegram",
    "linknumber",
    "blink",
    "checksum",
    "homekit",
    "homekit_start",
    "term",
    # Individual command functions
    "protocol_monitor",
    "conbus_download_msactiontable",
    "conbus_download_actiontable",
    "send_blink_on_telegram",
    "send_blink_off_telegram",
    "conbus_blink_all",
    "blink_all_off",
    "blink_all_on",
    "show_config",
    "send_custom_telegram",
    "send_discover_telegram",
    "send_event_raw",
    "xp_output_on",
    "xp_output_off",
    "xp_output_status",
    "xp_module_state",
    "scan_module",
    "query_datapoint",
    "query_all_datapoints",
    "send_raw_telegrams",
    "receive_telegrams",
    "set_linknumber_command",
    "get_linknumber_command",
    "set_modulenumber_command",
    "get_modulenumber_command",
    "get_autoreport_command",
    "set_autoreport_command",
    "xp_lightlevel_set",
    "xp_lightlevel_off",
    "xp_lightlevel_on",
    "xp_lightlevel_get",
    "blink_on",
    "blink_off",
    "parse_any_telegram",
    "validate_telegram",
    "generate_discover",
    "generate_set_link_number",
    "generate_read_link_number",
    "generate_version_request",
    "calculate_checksum",
    "validate_checksum",
]

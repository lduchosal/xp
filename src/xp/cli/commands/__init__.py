"""Command modules for XP CLI."""

# Main command groups
from xp.cli.commands.api_start_commands import start_api_server
from xp.cli.commands.conbus import (
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
from xp.cli.commands.conbus_actiontable_commands import conbus_download_actiontable

# Individual command functions that attach to groups
from xp.cli.commands.conbus_autoreport_commands import (
    get_autoreport_command,
    set_autoreport_command,
)
from xp.cli.commands.conbus_blink_commands import (
    blink_all_off,
    blink_all_on,
    conbus_blink_all,
    send_blink_off_telegram,
    send_blink_on_telegram,
)
from xp.cli.commands.conbus_config_commands import show_config
from xp.cli.commands.conbus_custom_commands import send_custom_telegram
from xp.cli.commands.conbus_datapoint_commands import (
    query_all_datapoints,
    query_datapoint,
)
from xp.cli.commands.conbus_discover_commands import send_discover_telegram
from xp.cli.commands.conbus_lightlevel_commands import (
    xp_lightlevel_get,
    xp_lightlevel_off,
    xp_lightlevel_on,
    xp_lightlevel_set,
)
from xp.cli.commands.conbus_linknumber_commands import (
    get_linknumber_command,
    set_linknumber_command,
)
from xp.cli.commands.conbus_msactiontable_commands import conbus_download_msactiontable
from xp.cli.commands.conbus_output_commands import (
    xp_module_state,
    xp_output_off,
    xp_output_on,
    xp_output_status,
)
from xp.cli.commands.conbus_raw_commands import send_raw_telegrams
from xp.cli.commands.conbus_receive_commands import receive_telegrams
from xp.cli.commands.conbus_scan_commands import scan_module
from xp.cli.commands.file_commands import file
from xp.cli.commands.homekit import homekit
from xp.cli.commands.homekit_start_commands import homekit_start
from xp.cli.commands.module_commands import module
from xp.cli.commands.reverse_proxy_commands import reverse_proxy
from xp.cli.commands.server_commands import server
from xp.cli.commands.telegram import blink, checksum, linknumber, telegram
from xp.cli.commands.telegram_blink_commands import blink_off, blink_on
from xp.cli.commands.telegram_checksum_commands import (
    calculate_checksum,
    validate_checksum,
)
from xp.cli.commands.telegram_discover_commands import generate_discover
from xp.cli.commands.telegram_linknumber_commands import (
    generate_read_link_number,
    generate_set_link_number,
)
from xp.cli.commands.telegram_parse_commands import (
    parse_any_telegram,
    validate_telegram,
)
from xp.cli.commands.telegram_version_commands import generate_version_request

__all__ = [
    # Main command groups
    "conbus",
    "conbus_blink",
    "conbus_output",
    "conbus_datapoint",
    "conbus_linknumber",
    "conbus_autoreport",
    "conbus_lightlevel",
    "conbus_msactiontable",
    "conbus_actiontable",
    "file",
    "module",
    "reverse_proxy",
    "server",
    "telegram",
    "linknumber",
    "blink",
    "checksum",
    "start_api_server",
    "homekit",
    "homekit_start",
    # Individual command functions
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

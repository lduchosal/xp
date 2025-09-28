"""Command modules for XP CLI."""

# Main command groups
from .conbus import (
    conbus,
    conbus_blink,
    conbus_output,
    conbus_datapoint,
    conbus_linknumber,
    conbus_autoreport,
    conbus_lightlevel,
    conbus_msactiontable,
    conbus_actiontable,
)
from .file_commands import file
from .module_commands import module
from .reverse_proxy_commands import reverse_proxy
from .server_commands import server
from .telegram import telegram, linknumber, blink, checksum
from .api_start_commands import start_api_server
from .homekit import homekit
from .homekit_start_commands import homekit_start

# Individual command functions that attach to groups
from .conbus_autoreport_commands import get_autoreport_command, set_autoreport_command

from .conbus_blink_commands import (
    send_blink_on_telegram,
    send_blink_off_telegram,
    conbus_blink_all,
    blink_all_off,
    blink_all_on,
)
from .conbus_config_commands import show_config
from .conbus_custom_commands import send_custom_telegram
from .conbus_datapoint_commands import query_datapoint, query_all_datapoints
from .conbus_discover_commands import send_discover_telegram
from .conbus_output_commands import (
    xp_output_on,
    xp_output_off,
    xp_output_status,
    xp_module_state,
)
from .conbus_msactiontable_commands import conbus_download_msactiontable
from .conbus_actiontable_commands import conbus_download_actiontable
from .conbus_scan_commands import scan_module
from .conbus_raw_commands import send_raw_telegrams
from .conbus_receive_commands import receive_telegrams
from .conbus_linknumber_commands import set_linknumber_command, get_linknumber_command
from .conbus_lightlevel_commands import (
    xp_lightlevel_set,
    xp_lightlevel_off,
    xp_lightlevel_on,
    xp_lightlevel_get,
)

from .telegram_blink_commands import blink_on, blink_off
from .telegram_parse_commands import parse_any_telegram, validate_telegram
from .telegram_discover_commands import generate_discover
from .telegram_linknumber_commands import (
    generate_set_link_number,
    generate_read_link_number,
)
from .telegram_version_commands import generate_version_request
from .telegram_checksum_commands import calculate_checksum, validate_checksum

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

"""Conbus export response model."""

from dataclasses import dataclass, field
from typing import Optional

from xp.models.config.conson_module_config import ConsonModuleListConfig


@dataclass
class ConbusExportResponse:
    """
    Response from Conbus export operation.

    Attributes:
        success: Whether the operation was successful.
        config: Exported module configuration list.
        device_count: Number of devices exported.
        actiontable_count: Number of action tables downloaded.
        actiontable_failed: Number of action table downloads that failed.
        output_file: Path to output file.
        export_status: Export status (OK, PARTIAL_ACTIONTABLE, FAILED_TIMEOUT, etc.).
        error: Error message if operation failed.
        sent_telegrams: List of telegrams sent during export.
        received_telegrams: List of telegrams received during export.
    """

    success: bool
    config: Optional[ConsonModuleListConfig] = None
    device_count: int = 0
    actiontable_count: int = 0
    actiontable_failed: int = 0
    output_file: str = "export.yml"
    export_status: str = "OK"
    error: Optional[str] = None
    sent_telegrams: list[str] = field(default_factory=list)
    received_telegrams: list[str] = field(default_factory=list)

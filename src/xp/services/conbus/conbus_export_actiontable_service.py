"""Conbus export service for exporting device configurations."""

import asyncio
import logging
from pathlib import Path
from queue import Empty, SimpleQueue
from typing import Any, Optional, Tuple

import yaml
from psygnal import Signal

from xp.models.actiontable.actiontable_type import ActionTableType, ActionTableType2
from xp.models.conbus.conbus_export import ConbusExportResponse
from xp.models.config.conson_module_config import (
    ConsonModuleConfig,
    ConsonModuleListConfig,
)
from xp.services.conbus.actiontable.actiontable_download_service import (
    ActionTableDownloadService,
)


class ConbusActiontableExportService:
    """
    Service for exporting Conbus device configurations.

    Discovers all devices on the Conbus network and queries their configuration
    datapoints to generate a structured export file compatible with conson.yml format.

    Attributes:
        download_service: Download service for exporting device configurations.
        export_result: Final export result.
        export_status: Export status (OK, FAILED_TIMEOUT, etc.).
        on_progress: Signal emitted on device discovery (serial, current, total).
        on_device_actiontable_exported: Signal emitted when device export completes.
        on_finish: Signal emitted when export finishes.
        ACTIONTABLE_SEQUENCE: Sequence of actiontable to query for each device.
    """

    # Signals (class attributes)
    on_progress: Signal = Signal(str, str, int, int)  # serial, current, total
    on_device_actiontable_exported: Signal = Signal(
        ConsonModuleConfig, ActionTableType, str
    )
    on_finish: Signal = Signal(ConbusExportResponse)

    ACTIONTABLE_SEQUENCE = [
        ActionTableType2.ACTIONTABLE,
        ActionTableType2.MSACTIONTABLE,
    ]

    def __init__(
        self,
        download_service: ActionTableDownloadService,
        module_list: ConsonModuleListConfig,
    ) -> None:
        """
        Initialize the Conbus export service.

        Args:
            download_service: Protocol for downloading actiontables.
            module_list: module to export.
        """
        self.logger = logging.getLogger(__name__)
        self.download_service = download_service
        self._module_list: ConsonModuleListConfig = module_list
        self._module_dic: dict[str, ConsonModuleConfig] = {
            module.serial_number: module for module in module_list.root
        }
        # State management
        self.device_queue: SimpleQueue[Tuple[str, ActionTableType]] = (
            SimpleQueue()
        )  # FIFO
        for module in self._module_list.root:
            self.logger.info("Export module %s", module)
            if module.module_type.lower() == "xp20":
                self.device_queue.put(
                    (module.serial_number, ActionTableType.MSACTIONTABLE_XP20)
                )
            if module.module_type.lower() == "xp24":
                self.device_queue.put(
                    (module.serial_number, ActionTableType.MSACTIONTABLE_XP24)
                )
            if module.module_type.lower() == "xp33":
                self.device_queue.put(
                    (module.serial_number, ActionTableType.MSACTIONTABLE_XP33)
                )
            self.device_queue.put((module.serial_number, ActionTableType.ACTIONTABLE))

        self.logger.info("Export module %s", self.device_queue.qsize())

        self.current_module: Optional[ConsonModuleConfig] = None
        self.current_actiontable_type: Optional[ActionTableType] = None
        self.export_result = ConbusExportResponse(success=False)
        self.export_status = "OK"

    def on_module_actiontable_received(
        self, actiontable: Any, short_actiontable: list[str]
    ) -> None:
        """
        Handle actiontable received event.

        Args:
            actiontable: Full actiontable data.
            short_actiontable: Short representation of the actiontable.
        """
        if not self.current_actiontable_type:
            self._fail("Invalid state (curent_actiontable_type)")
            return

        if not self.current_module:
            self._fail("Invalid state (current_module)")
            return

        if self.current_actiontable_type == ActionTableType.ACTIONTABLE:
            self.current_module.action_table = short_actiontable
        elif self.current_actiontable_type == ActionTableType.MSACTIONTABLE_XP20:
            self.current_module.xp20_msaction_table = short_actiontable
        elif self.current_actiontable_type == ActionTableType.MSACTIONTABLE_XP24:
            self.current_module.xp24_msaction_table = short_actiontable
        elif self.current_actiontable_type == ActionTableType.MSACTIONTABLE_XP33:
            self.current_module.xp33_msaction_table = short_actiontable

        self.on_device_actiontable_exported.emit(
            self.current_module, self.current_actiontable_type, short_actiontable
        )

    def on_module_finish(self) -> None:
        """Handle module export completion."""
        self._save_action_table()
        has_next_module = self.configure()
        if not has_next_module:
            self._succeed()

    def on_module_progress(self) -> None:
        """Handle module progress event and emit progress signal."""
        serial_number = (
            self.current_module.serial_number if self.current_module else "UNKNOWN"
        )
        current_actiontable_type = self.current_actiontable_type or "UNKNOWN"
        total_modules = len(self._module_list.root)
        current_index = total_modules - self.device_queue.qsize()

        self.on_progress.emit(
            serial_number, current_actiontable_type, current_index, total_modules
        )

    def on_module_error(self, error_message: str) -> None:
        """
        Handle module error event.

        Args:
            error_message: Error message from module.
        """
        self._fail(error_message)

    def _save_action_table(self) -> None:
        """Write export to YAML file."""
        self.logger.info("Saving action table")

        if not self._module_list:
            self._fail("FAILED_NO_DEVICES")
            return

        try:
            # Write to file
            path = "export.yml"
            output_path = Path(path)

            # Use Pydantic's model_dump to serialize, excluding only internal fields
            data = self._module_list.model_dump(
                exclude={
                    "root": {
                        "__all__": {
                            "enabled",
                            "conbus_ip",
                            "conbus_port",
                        }
                    }
                },
                exclude_none=True,
            )

            # Export as list at root level (not wrapped in 'root:' key)
            modules_list = data.get("root", [])

            with output_path.open("w") as f:
                # Dump each module separately with blank lines between them
                for i, module in enumerate(modules_list):
                    # Add blank line before each module except the first
                    if i > 0:
                        f.write("\n")

                    # Dump single item as list element
                    yaml_str = yaml.safe_dump(
                        [module],
                        default_flow_style=False,
                        sort_keys=False,
                        allow_unicode=True,
                    )
                    # Remove the trailing newline and write
                    f.write(yaml_str.rstrip("\n") + "\n")

            self.logger.info(f"Export written to {path}")
            self.export_result.output_file = path

        except Exception as e:
            self._fail(f"Failed to create export: {e}")

    def configure(self) -> bool:
        """
        Configure export service.

        Returns:
            True if there is a module to export, False otherwise.
        """
        self.download_service.reset()
        try:
            (current_serial_number, self.current_actiontable_type) = (
                self.device_queue.get_nowait()
            )
        except Empty:
            return False

        self.current_module = self._module_dic[current_serial_number]
        if not (self.current_module or self.current_actiontable_type):
            self.logger.error("No module to export")
            return False

        self.logger.info(
            f"Downloading {self.current_module.serial_number} / {self.current_actiontable_type}"
        )
        self.download_service.configure(
            self.current_module.serial_number,
            self.current_actiontable_type,
        )
        self.download_service.do_connect()
        return True

    def set_event_loop(self, event_loop: asyncio.AbstractEventLoop) -> None:
        """
        Set event loop for async operations.

        Args:
            event_loop: Event loop to use.
        """
        self.logger.debug("Set event loop")
        self.download_service.set_event_loop(event_loop)

    def set_timeout(self, timeout_seconds: float) -> None:
        """
        Set timeout.

        Args:
            timeout_seconds: Timeout in seconds.
        """
        self.download_service.set_timeout(timeout_seconds)

    def start_reactor(self) -> None:
        """Start the reactor."""
        self.download_service.start_reactor()

    def stop_reactor(self) -> None:
        """Stop the reactor."""
        self.download_service.stop_reactor()

    def __enter__(self) -> "ConbusActiontableExportService":
        """
        Enter context manager.

        Returns:
            Self for context manager protocol.
        """
        # Reset state for reuse
        self.export_result = ConbusExportResponse(success=False)
        self.export_status = "OK"
        self._connect_signals()
        return self

    def __exit__(
        self, _exc_type: Optional[type], _exc_val: Optional[Exception], _exc_tb: Any
    ) -> None:
        """Exit context manager and disconnect signals."""
        self._disconnect_signals()
        self.stop_reactor()

    def _connect_signals(self) -> None:
        """Connect download service signals to handlers."""
        self.download_service.on_actiontable_received.connect(
            self.on_module_actiontable_received
        )
        self.download_service.on_finish.connect(self.on_module_finish)
        self.download_service.on_progress.connect(self.on_module_progress)
        self.download_service.on_error.connect(self.on_module_error)

    def _disconnect_signals(self) -> None:
        """Disconnect download service signals from handlers."""
        self.download_service.on_actiontable_received.disconnect(
            self.on_module_actiontable_received
        )
        self.download_service.on_finish.disconnect(self.on_module_finish)
        self.download_service.on_progress.disconnect(self.on_module_progress)
        self.download_service.on_error.disconnect(self.on_module_error)

        self.on_progress.disconnect()
        self.on_device_actiontable_exported.disconnect()
        self.on_finish.disconnect()

    def _fail(self, error: str) -> None:
        """
        Handle export failure.

        Args:
            error: Error message.
        """
        self.logger.error(error)
        self.export_result.success = False
        self.export_result.error = error
        self.export_result.export_status = "FAILED"
        self.on_finish.emit(self.export_result)

    def _succeed(self) -> None:
        """Handle export success."""
        self.logger.info("Export succeed")
        self.export_result.success = True
        self.export_result.error = None
        self.export_result.export_status = "OK"
        self.on_finish.emit(self.export_result)

"""Conbus export service for exporting device configurations."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

import yaml
from psygnal import Signal

from xp.models.conbus.conbus_export import ConbusExportResponse
from xp.models.config.conson_module_config import (
    ConsonModuleConfig,
    ConsonModuleListConfig,
)
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol
from xp.services.telegram.telegram_service import TelegramService


class ConbusExportService:
    """
    Service for exporting Conbus device configurations.

    Discovers all devices on the Conbus network and queries their configuration
    datapoints to generate a structured export file compatible with conson.yml format.

    Attributes:
        conbus_protocol: Protocol for Conbus communication.
        discovered_devices: List of discovered device serial numbers.
        device_configs: Device configurations (ConsonModuleConfig instances).
        export_result: Final export result.
        export_status: Export status (OK, FAILED_TIMEOUT, etc.).
        on_progress: Signal emitted on device discovery (serial, current, total).
        on_device_exported: Signal emitted when device export completes.
        on_finish: Signal emitted when export finishes.
        DATAPOINT_SEQUENCE: Sequence of 7 datapoints to query for each device.
    """

    # Signals (class attributes)
    on_progress: Signal = Signal(str, int, int)  # serial, current, total
    on_device_exported: Signal = Signal(ConsonModuleConfig)
    on_finish: Signal = Signal(ConbusExportResponse)

    # Datapoint sequence to query for each device
    DATAPOINT_SEQUENCE = [
        DataPointType.MODULE_TYPE,
        DataPointType.MODULE_TYPE_CODE,
        DataPointType.LINK_NUMBER,
        DataPointType.MODULE_NUMBER,
        DataPointType.SW_VERSION,
        DataPointType.HW_VERSION,
        DataPointType.AUTO_REPORT_STATUS,
    ]

    def __init__(
        self, conbus_protocol: ConbusEventProtocol, telegram_service: TelegramService
    ) -> None:
        """
        Initialize the Conbus export service.

        Args:
            conbus_protocol: Protocol for Conbus communication.
            telegram_service: TelegramService for telegram parsing.
        """
        self.logger = logging.getLogger(__name__)
        self.conbus_protocol = conbus_protocol
        self.telegram_service = telegram_service

        # State management
        self.discovered_devices: list[str] = []
        self.device_configs: dict[str, ConsonModuleConfig] = {}
        self.export_result = ConbusExportResponse(success=False)
        self.export_status = "OK"
        self._finalized = False  # Track if export has been finalized

        # Connect protocol signals
        self.conbus_protocol.on_connection_made.connect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.connect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.connect(self.telegram_received)
        self.conbus_protocol.on_timeout.connect(self.timeout)
        self.conbus_protocol.on_failed.connect(self.failed)

    def connection_made(self) -> None:
        """Handle connection established event."""
        self.logger.debug("Connection established, starting discovery")

        # Send DISCOVERY telegram
        self.conbus_protocol.send_telegram(
            telegram_type=TelegramType.SYSTEM,
            serial_number="0000000000",
            system_function=SystemFunction.DISCOVERY,
            data_value="00",
        )

    def telegram_sent(self, telegram: str) -> None:
        """
        Handle telegram sent event.

        Args:
            telegram: Telegram that was sent.
        """
        self.export_result.sent_telegrams.append(telegram)

    def telegram_received(self, event: TelegramReceivedEvent) -> None:
        """
        Handle telegram received event.

        Args:
            event: Telegram received event.
        """
        self.export_result.received_telegrams.append(event.telegram)

        # Only process valid reply telegrams
        if not event.checksum_valid or event.telegram_type != TelegramType.REPLY.value:
            return

        # Parse telegram using TelegramService
        try:
            parsed: ReplyTelegram = self.telegram_service.parse_reply_telegram(
                event.frame
            )
        except Exception as e:
            self.logger.debug(f"Failed to parse telegram: {e}")
            return

        # Check for discovery response (F01D)
        if parsed.system_function == SystemFunction.DISCOVERY:
            self._handle_discovery_response(parsed.serial_number)

        # Check for datapoint response (F02D)
        elif parsed.system_function == SystemFunction.READ_DATAPOINT:
            if parsed.datapoint_type and parsed.data_value:
                self._handle_datapoint_response(
                    parsed.serial_number, parsed.datapoint_type.value, parsed.data_value
                )

    def _handle_discovery_response(self, serial_number: str) -> None:
        """
        Handle discovery response and query all datapoints.

        Args:
            serial_number: Serial number of discovered device.
        """
        if serial_number in self.discovered_devices:
            self.logger.debug(f"Ignoring duplicate discovery: {serial_number}")
            return

        self.logger.debug(f"Device discovered: {serial_number}")
        self.discovered_devices.append(serial_number)

        # Create ConsonModuleConfig with placeholder values for required fields
        module = ConsonModuleConfig(
            name="UNKNOWN",  # Will be updated when link_number arrives
            serial_number=serial_number,
            module_type="UNKNOWN",  # Required field
            module_type_code=0,  # Required field
            link_number=0,  # Required field
        )
        self.device_configs[serial_number] = module

        # Emit progress signal
        current = len(self.discovered_devices)
        total = current  # We don't know total until timeout
        self.on_progress.emit(serial_number, current, total)

        # Send all datapoint queries immediately (protocol handles throttling)
        self.logger.debug(
            f"Sending {len(self.DATAPOINT_SEQUENCE)} queries for {serial_number}"
        )
        for datapoint in self.DATAPOINT_SEQUENCE:
            self.conbus_protocol.send_telegram(
                telegram_type=TelegramType.SYSTEM,
                serial_number=serial_number,
                system_function=SystemFunction.READ_DATAPOINT,
                data_value=datapoint.value,
            )

    def _handle_datapoint_response(
        self, serial_number: str, datapoint_code: str, value: str
    ) -> None:
        """
        Handle datapoint response and store value.

        Args:
            serial_number: Serial number of device.
            datapoint_code: Datapoint type code.
            value: Datapoint value.
        """
        if serial_number not in self.device_configs:
            self.logger.warning(
                f"Received datapoint for unknown device: {serial_number}"
            )
            return

        self.logger.debug(f"Datapoint {datapoint_code}={value} for {serial_number}")

        # Store value in device config
        datapoint = DataPointType.from_code(datapoint_code)
        if datapoint:
            self._store_datapoint_value(serial_number, datapoint, value)
            self._check_device_complete(serial_number)
        else:
            self.logger.warning(f"Unknown datapoint code: {datapoint_code}")

    def _store_datapoint_value(
        self, serial_number: str, datapoint: DataPointType, value: str
    ) -> None:
        """
        Store datapoint value in device config.

        Args:
            serial_number: Serial number of device.
            datapoint: Datapoint type.
            value: Datapoint value.
        """
        module = self.device_configs[serial_number]

        try:
            if datapoint == DataPointType.MODULE_TYPE:
                module.module_type = value
            elif datapoint == DataPointType.MODULE_TYPE_CODE:
                module.module_type_code = int(value)
            elif datapoint == DataPointType.LINK_NUMBER:
                link = int(value)
                module.link_number = link
                module.name = f"A{link}"
            elif datapoint == DataPointType.MODULE_NUMBER:
                module.module_number = int(value)
            elif datapoint == DataPointType.SW_VERSION:
                module.sw_version = value
            elif datapoint == DataPointType.HW_VERSION:
                module.hw_version = value
            elif datapoint == DataPointType.AUTO_REPORT_STATUS:
                module.auto_report_status = value
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Invalid value '{value}' for {datapoint.name}: {e}")

    def _is_device_complete(self, serial_number: str) -> bool:
        """
        Check if a device has all required datapoints.

        Args:
            serial_number: Serial number of device.

        Returns:
            True if device is complete, False otherwise.
        """
        module = self.device_configs[serial_number]
        return all(
            [
                module.module_type not in ("UNKNOWN", None, ""),
                module.module_type_code is not None and module.module_type_code > 0,
                module.link_number is not None and module.link_number > 0,
                module.sw_version is not None,
                module.hw_version is not None,
                module.auto_report_status is not None,
                module.module_number is not None,
            ]
        )

    def _check_device_complete(self, serial_number: str) -> None:
        """
        Check if device has all datapoints and emit completion signal.

        Args:
            serial_number: Serial number of device.
        """
        if self._is_device_complete(serial_number):
            self.logger.debug(f"Device {serial_number} complete (7/7 datapoints)")
            module = self.device_configs[serial_number]
            self.on_device_exported.emit(module)

            # Check if all devices complete
            if all(self._is_device_complete(sn) for sn in self.discovered_devices):
                self.logger.debug("All devices complete")
                self._finalize_export()

    def _finalize_export(self) -> None:
        """Finalize export and write file."""
        # Only finalize once
        if self._finalized:
            return

        self._finalized = True
        self.logger.info("Finalizing export")

        if not self.discovered_devices:
            self.export_status = "FAILED_NO_DEVICES"
            self.export_result.success = False
            self.export_result.error = "No devices found"
            self.export_result.export_status = self.export_status
            self.on_finish.emit(self.export_result)
            return

        # Convert dict values to list (already ConsonModuleConfig instances!)
        modules = list(self.device_configs.values())

        # Sort modules by link_number
        modules.sort(key=lambda m: m.link_number if m.link_number is not None else 999)

        # Create ConsonModuleListConfig
        try:
            module_list = ConsonModuleListConfig(root=modules)
            self.export_result.config = module_list
            self.export_result.device_count = len(modules)

            # Write to file
            self._write_export_file("export.yml")

            self.export_result.success = True
            self.export_result.export_status = self.export_status
            self.on_finish.emit(self.export_result)

        except Exception as e:
            self.logger.error(f"Failed to create export: {e}")
            self.export_status = "FAILED_WRITE"
            self.export_result.success = False
            self.export_result.error = str(e)
            self.export_result.export_status = self.export_status
            self.on_finish.emit(self.export_result)

    def _write_export_file(self, path: str) -> None:
        """
        Write export to YAML file.

        Args:
            path: Output file path.

        Raises:
            Exception: If file write fails.
        """
        try:
            output_path = Path(path)

            if self.export_result.config:
                # Use Pydantic's model_dump to serialize, excluding only internal fields
                data = self.export_result.config.model_dump(
                    exclude={
                        "root": {
                            "__all__": {
                                "enabled",
                                "conbus_ip",
                                "conbus_port",
                                "action_table",
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
            self.logger.error(f"Failed to write export file: {e}")
            self.export_status = "FAILED_WRITE"
            raise

    def timeout(self) -> None:
        """Handle timeout event."""
        timeout = self.conbus_protocol.timeout_seconds
        self.logger.info(f"Export timeout after {timeout}s")

        # Check if any devices incomplete
        incomplete = [
            sn for sn in self.discovered_devices if not self._is_device_complete(sn)
        ]

        if incomplete:
            self.logger.warning(f"Partial export: {len(incomplete)} incomplete devices")
            self.export_status = "FAILED_TIMEOUT"

        self._finalize_export()

    def failed(self, message: str) -> None:
        """
        Handle connection failure event.

        Args:
            message: Failure message.
        """
        self.logger.error(f"Connection failed: {message}")
        self.export_status = "FAILED_CONNECTION"
        self.export_result.success = False
        self.export_result.error = message
        self.export_result.export_status = self.export_status
        self.on_finish.emit(self.export_result)

    def set_timeout(self, timeout_seconds: float) -> None:
        """
        Set timeout for export operation.

        Args:
            timeout_seconds: Timeout in seconds.
        """
        self.logger.debug(f"Set timeout: {timeout_seconds}s")
        self.conbus_protocol.timeout_seconds = timeout_seconds

    def set_event_loop(self, event_loop: asyncio.AbstractEventLoop) -> None:
        """
        Set event loop for async operations.

        Args:
            event_loop: Event loop to use.
        """
        self.logger.debug("Set event loop")
        self.conbus_protocol.set_event_loop(event_loop)

    def start_reactor(self) -> None:
        """Start the reactor."""
        self.conbus_protocol.start_reactor()

    def stop_reactor(self) -> None:
        """Stop the reactor."""
        self.conbus_protocol.stop_reactor()

    def __enter__(self) -> "ConbusExportService":
        """
        Enter context manager.

        Returns:
            Self for context manager protocol.
        """
        # Reset state for reuse
        self.discovered_devices = []
        self.device_configs = {}
        self.export_result = ConbusExportResponse(success=False)
        self.export_status = "OK"
        self._finalized = False
        return self

    def __exit__(
        self, _exc_type: Optional[type], _exc_val: Optional[Exception], _exc_tb: Any
    ) -> None:
        """Exit context manager and disconnect signals."""
        self.conbus_protocol.on_connection_made.disconnect(self.connection_made)
        self.conbus_protocol.on_telegram_sent.disconnect(self.telegram_sent)
        self.conbus_protocol.on_telegram_received.disconnect(self.telegram_received)
        self.conbus_protocol.on_timeout.disconnect(self.timeout)
        self.conbus_protocol.on_failed.disconnect(self.failed)
        self.on_progress.disconnect()
        self.on_device_exported.disconnect()
        self.on_finish.disconnect()
        self.stop_reactor()

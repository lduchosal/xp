"""Conbus export service for exporting device configurations."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

import yaml
from psygnal import Signal

from xp.models.conbus.conbus_export import ConbusExportResponse
from xp.models.homekit.homekit_conson_config import (
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
    """Service for exporting Conbus device configurations.

    Discovers all devices on the Conbus network and queries their configuration
    datapoints to generate a structured export file compatible with conson.yml format.

    Attributes:
        conbus_protocol: Protocol for Conbus communication.
        discovered_devices: List of discovered device serial numbers.
        device_configs: Partial device configurations being built.
        device_datapoints_received: Set of datapoints received per device.
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

    def __init__(self, conbus_protocol: ConbusEventProtocol) -> None:
        """Initialize the Conbus export service.

        Args:
            conbus_protocol: Protocol for Conbus communication.
        """
        self.logger = logging.getLogger(__name__)
        self.conbus_protocol = conbus_protocol
        self.telegram_service = TelegramService()

        # State management
        self.discovered_devices: list[str] = []
        self.device_configs: dict[str, dict[str, Any]] = {}
        self.device_datapoints_received: dict[str, set[str]] = {}
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
        """Handle telegram sent event.

        Args:
            telegram: Telegram that was sent.
        """
        self.export_result.sent_telegrams.append(telegram)

    def telegram_received(self, event: TelegramReceivedEvent) -> None:
        """Handle telegram received event.

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
        """Handle discovery response and query all datapoints.

        Args:
            serial_number: Serial number of discovered device.
        """
        if serial_number in self.discovered_devices:
            self.logger.debug(f"Ignoring duplicate discovery: {serial_number}")
            return

        self.logger.debug(f"Device discovered: {serial_number}")
        self.discovered_devices.append(serial_number)
        self.device_configs[serial_number] = {"serial_number": serial_number}
        self.device_datapoints_received[serial_number] = set()

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
        """Handle datapoint response and store value.

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
            self.device_datapoints_received[serial_number].add(datapoint_code)
            self._check_device_complete(serial_number)
        else:
            self.logger.warning(f"Unknown datapoint code: {datapoint_code}")

    def _store_datapoint_value(
        self, serial_number: str, datapoint: DataPointType, value: str
    ) -> None:
        """Store datapoint value in device config.

        Args:
            serial_number: Serial number of device.
            datapoint: Datapoint type.
            value: Datapoint value.
        """
        config = self.device_configs[serial_number]

        if datapoint == DataPointType.MODULE_TYPE:
            config["module_type"] = value
        elif datapoint == DataPointType.MODULE_TYPE_CODE:
            try:
                config["module_type_code"] = int(value)
            except ValueError:
                self.logger.warning(f"Invalid module_type_code: {value}")
        elif datapoint == DataPointType.LINK_NUMBER:
            try:
                config["link_number"] = int(value)
            except ValueError:
                self.logger.warning(f"Invalid link_number: {value}")
        elif datapoint == DataPointType.MODULE_NUMBER:
            try:
                config["module_number"] = int(value)
            except ValueError:
                self.logger.warning(f"Invalid module_number: {value}")
        elif datapoint == DataPointType.SW_VERSION:
            config["sw_version"] = value
        elif datapoint == DataPointType.HW_VERSION:
            config["hw_version"] = value
        elif datapoint == DataPointType.AUTO_REPORT_STATUS:
            config["auto_report_status"] = value

    def _check_device_complete(self, serial_number: str) -> None:
        """Check if device has all datapoints and emit completion signal.

        Args:
            serial_number: Serial number of device.
        """
        received = self.device_datapoints_received[serial_number]
        expected = {dp.value for dp in self.DATAPOINT_SEQUENCE}

        if received == expected:
            self.logger.debug(f"Device {serial_number} complete (7/7 datapoints)")
            config = self.device_configs[serial_number]

            # Build ConsonModuleConfig with name based on link_number
            try:
                # Add required 'name' field as A{link_number}
                if "name" not in config:
                    link_number = config.get("link_number", 0)
                    config["name"] = f"A{link_number}"
                module_config = ConsonModuleConfig(**config)
                self.on_device_exported.emit(module_config)
            except Exception as e:
                self.logger.error(f"Failed to build config for {serial_number}: {e}")

            # Check if all devices complete
            if all(
                len(self.device_datapoints_received[sn]) == len(self.DATAPOINT_SEQUENCE)
                for sn in self.discovered_devices
            ):
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

        # Build module list (including partial devices)
        modules = []
        for serial_number in self.discovered_devices:
            config = self.device_configs[serial_number].copy()
            try:
                # Add required 'name' field as A{link_number} if not present
                if "name" not in config:
                    link_number = config.get("link_number", 0)
                    config["name"] = f"A{link_number}"
                # Only include fields that were received
                module_config = ConsonModuleConfig(**config)
                modules.append(module_config)
            except Exception as e:
                self.logger.warning(f"Partial device {serial_number}: {e}")

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
        """Write export to YAML file.

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
            sn
            for sn in self.discovered_devices
            if len(self.device_datapoints_received[sn]) < len(self.DATAPOINT_SEQUENCE)
        ]

        if incomplete:
            self.logger.warning(f"Partial export: {len(incomplete)} incomplete devices")
            self.export_status = "FAILED_TIMEOUT"

        self._finalize_export()

    def failed(self, message: str) -> None:
        """Handle connection failure event.

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
        """Set timeout for export operation.

        Args:
            timeout_seconds: Timeout in seconds.
        """
        self.logger.debug(f"Set timeout: {timeout_seconds}s")
        self.conbus_protocol.timeout_seconds = timeout_seconds

    def set_event_loop(self, event_loop: asyncio.AbstractEventLoop) -> None:
        """Set event loop for async operations.

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
        """Enter context manager.

        Returns:
            Self for context manager protocol.
        """
        # Reset state for reuse
        self.discovered_devices = []
        self.device_configs = {}
        self.device_datapoints_received = {}
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

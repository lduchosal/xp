# Copyright (c) 2025 ldvchosal
"""Unit tests for ConbusExportService."""

from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.conbus.conbus_export_service import ConbusExportService
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol
from xp.services.telegram.telegram_service import TelegramParsingError

SERIAL_A = "0012345001"
SERIAL_B = "0012345002"
DATAPOINT_QUERY_COUNT = 7
DEVICE_COUNT_TWO = 2
UPDATED_TIMEOUT_SECONDS = 5.0

# Datapoint replies forming a complete device configuration.
COMPLETE_DATAPOINTS: dict[DataPointType, str] = {
    DataPointType.MODULE_TYPE: "XP24",
    DataPointType.MODULE_TYPE_CODE: "07",
    DataPointType.LINK_NUMBER: "02",
    DataPointType.MODULE_NUMBER: "05",
    DataPointType.SW_VERSION: "XP24_V0.34.03",
    DataPointType.HW_VERSION: "XP24_HW_V1.00",
    DataPointType.AUTO_REPORT_STATUS: "ON",
}
EXPECTED_MODULE_TYPE_CODE = 7
EXPECTED_LINK_NUMBER = 2
EXPECTED_MODULE_NUMBER = 5


def make_reply_event(
    protocol: ConbusEventProtocol,
    serial_number: str,
    *,
    checksum_valid: bool = True,
    telegram_type: str = TelegramType.REPLY.value,
) -> TelegramReceivedEvent:
    """Build a TelegramReceivedEvent suitable for telegram_received tests.

    Returns:
        A TelegramReceivedEvent suitable for telegram_received tests.

    """
    frame = f"<R{serial_number}F02D00XP24FF>"
    return TelegramReceivedEvent.model_construct(
        protocol=protocol,
        frame=frame,
        telegram=frame[1:-1],
        payload=f"R{serial_number}F02D00XP24",
        telegram_type=telegram_type,
        serial_number=serial_number,
        checksum="FF",
        checksum_valid=checksum_valid,
    )


def receive_discovery(
    service: ConbusExportService,
    telegram_service: Mock,
    serial_number: str,
) -> None:
    """Inject a discovery reply telegram into the service."""
    telegram_service.parse_reply_telegram.return_value = ReplyTelegram(
        serial_number=serial_number,
        system_function=SystemFunction.DISCOVERY,
        raw_telegram=f"<R{serial_number}F01DFF>",
        checksum="FF",
    )
    service.telegram_received(make_reply_event(service.conbus_protocol, serial_number))


def receive_datapoint(
    service: ConbusExportService,
    telegram_service: Mock,
    serial_number: str,
    datapoint: DataPointType,
    value: str,
) -> None:
    """Inject a datapoint reply telegram into the service."""
    telegram_service.parse_reply_telegram.return_value = ReplyTelegram(
        serial_number=serial_number,
        system_function=SystemFunction.READ_DATAPOINT,
        raw_telegram=f"<R{serial_number}F02D{datapoint.value}{value}FF>",
        checksum="FF",
        datapoint_type=datapoint,
        data_value=value,
    )
    service.telegram_received(make_reply_event(service.conbus_protocol, serial_number))


def complete_device(
    service: ConbusExportService,
    telegram_service: Mock,
    serial_number: str,
    datapoint_values: dict[DataPointType, str] | None = None,
) -> None:
    """Feed a full set of datapoint replies for one device."""
    values = COMPLETE_DATAPOINTS if datapoint_values is None else datapoint_values
    for datapoint, value in values.items():
        receive_datapoint(service, telegram_service, serial_number, datapoint, value)


class TestConbusExportService:
    """Unit tests for ConbusExportService functionality."""

    @pytest.fixture
    def mock_conbus_protocol(self) -> Mock:
        """Create a mock ConbusEventProtocol.

        Returns:
            A mock ConbusEventProtocol.

        """
        mock_protocol = Mock()
        mock_protocol.on_connection_made = Mock()
        mock_protocol.on_telegram_sent = Mock()
        mock_protocol.on_telegram_received = Mock()
        mock_protocol.on_timeout = Mock()
        mock_protocol.on_failed = Mock()
        mock_protocol.on_connection_made.connect = Mock()
        mock_protocol.on_telegram_sent.connect = Mock()
        mock_protocol.on_telegram_received.connect = Mock()
        mock_protocol.on_timeout.connect = Mock()
        mock_protocol.on_failed.connect = Mock()
        mock_protocol.on_connection_made.disconnect = Mock()
        mock_protocol.on_telegram_sent.disconnect = Mock()
        mock_protocol.on_telegram_received.disconnect = Mock()
        mock_protocol.on_timeout.disconnect = Mock()
        mock_protocol.on_failed.disconnect = Mock()
        mock_protocol.send_telegram = Mock()
        mock_protocol.set_event_loop = Mock()
        mock_protocol.start_reactor = Mock()
        mock_protocol.stop_reactor = Mock()
        mock_protocol.timeout_seconds = 0.25
        return mock_protocol

    @pytest.fixture
    def mock_telegram_service(self) -> Mock:
        """Create a mock telegram service.

        Returns:
            A mock telegram service.

        """
        return Mock()

    @pytest.fixture
    def service(
        self, mock_conbus_protocol: Mock, mock_telegram_service: Mock
    ) -> ConbusExportService:
        """Create service instance with test dependencies.

        Returns:
            Service instance with test dependencies.

        """
        return ConbusExportService(
            conbus_protocol=mock_conbus_protocol,
            telegram_service=mock_telegram_service,
        )

    def test_service_initialization(
        self, service: ConbusExportService, mock_conbus_protocol: Mock
    ) -> None:
        """Test service can be initialized with required dependencies."""
        assert service.discovered_devices == []
        assert service.device_configs == {}
        assert service.export_result.success is False
        assert service.export_status == "OK"
        # Verify signal connections
        mock_conbus_protocol.on_connection_made.connect.assert_called_once()
        mock_conbus_protocol.on_telegram_sent.connect.assert_called_once()
        mock_conbus_protocol.on_telegram_received.connect.assert_called_once()
        mock_conbus_protocol.on_timeout.connect.assert_called_once()
        mock_conbus_protocol.on_failed.connect.assert_called_once()

    def test_connection_made_sends_discovery(
        self, service: ConbusExportService, mock_conbus_protocol: Mock
    ) -> None:
        """Test connection_made sends a broadcast DISCOVERY telegram."""
        service.connection_made()

        mock_conbus_protocol.send_telegram.assert_called_once_with(
            telegram_type=TelegramType.SYSTEM,
            serial_number="0000000000",
            system_function=SystemFunction.DISCOVERY,
            data_value="00",
        )

    def test_telegram_sent_records_telegram(self, service: ConbusExportService) -> None:
        """Test telegram_sent appends the telegram to the export result."""
        telegram = "<S0000000000F01D00FA>"

        service.telegram_sent(telegram)

        assert service.export_result.sent_telegrams == [telegram]

    def test_telegram_received_ignores_invalid_checksum(
        self,
        service: ConbusExportService,
        mock_conbus_protocol: Mock,
        mock_telegram_service: Mock,
    ) -> None:
        """Test telegrams with invalid checksum are recorded but not parsed."""
        event = make_reply_event(mock_conbus_protocol, SERIAL_A, checksum_valid=False)

        service.telegram_received(event)

        assert service.export_result.received_telegrams == [event.telegram]
        mock_telegram_service.parse_reply_telegram.assert_not_called()
        assert service.discovered_devices == []

    def test_telegram_received_ignores_non_reply(
        self,
        service: ConbusExportService,
        mock_conbus_protocol: Mock,
        mock_telegram_service: Mock,
    ) -> None:
        """Test non-reply telegrams are recorded but not parsed."""
        event = make_reply_event(
            mock_conbus_protocol,
            SERIAL_A,
            telegram_type=TelegramType.EVENT.value,
        )

        service.telegram_received(event)

        assert service.export_result.received_telegrams == [event.telegram]
        mock_telegram_service.parse_reply_telegram.assert_not_called()

    def test_telegram_received_handles_parse_error(
        self,
        service: ConbusExportService,
        mock_conbus_protocol: Mock,
        mock_telegram_service: Mock,
    ) -> None:
        """Test parsing errors are swallowed and no device is registered."""
        mock_telegram_service.parse_reply_telegram.side_effect = TelegramParsingError(
            "invalid frame"
        )

        service.telegram_received(make_reply_event(mock_conbus_protocol, SERIAL_A))

        assert service.discovered_devices == []
        assert service.device_configs == {}

    def test_discovery_registers_device_and_queries_datapoints(
        self,
        service: ConbusExportService,
        mock_conbus_protocol: Mock,
        mock_telegram_service: Mock,
    ) -> None:
        """Test discovery reply registers the device and queries 7 datapoints."""
        progress_mock = Mock()
        service.on_progress.connect(progress_mock)

        receive_discovery(service, mock_telegram_service, SERIAL_A)

        assert service.discovered_devices == [SERIAL_A]
        module = service.device_configs[SERIAL_A]
        assert module.serial_number == SERIAL_A
        assert module.name == "UNKNOWN"
        assert module.module_type == "UNKNOWN"
        progress_mock.assert_called_once_with(SERIAL_A, 1, 1)
        # One READ_DATAPOINT query per datapoint in the sequence
        assert mock_conbus_protocol.send_telegram.call_count == DATAPOINT_QUERY_COUNT
        queried = [
            call.kwargs["data_value"]
            for call in mock_conbus_protocol.send_telegram.call_args_list
        ]
        expected = [
            datapoint.value for datapoint in ConbusExportService.DATAPOINT_SEQUENCE
        ]
        assert queried == expected

    def test_duplicate_discovery_is_ignored(
        self,
        service: ConbusExportService,
        mock_conbus_protocol: Mock,
        mock_telegram_service: Mock,
    ) -> None:
        """Test a duplicate discovery reply does not re-register the device."""
        progress_mock = Mock()
        service.on_progress.connect(progress_mock)

        receive_discovery(service, mock_telegram_service, SERIAL_A)
        receive_discovery(service, mock_telegram_service, SERIAL_A)

        assert service.discovered_devices == [SERIAL_A]
        progress_mock.assert_called_once()
        assert mock_conbus_protocol.send_telegram.call_count == DATAPOINT_QUERY_COUNT

    def test_datapoint_responses_update_module(
        self,
        service: ConbusExportService,
        mock_telegram_service: Mock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test datapoint replies are stored on the module config."""
        monkeypatch.chdir(tmp_path)
        receive_discovery(service, mock_telegram_service, SERIAL_A)

        complete_device(service, mock_telegram_service, SERIAL_A)

        module = service.device_configs[SERIAL_A]
        assert module.module_type == "XP24"
        assert module.module_type_code == EXPECTED_MODULE_TYPE_CODE
        assert module.link_number == EXPECTED_LINK_NUMBER
        assert module.name == f"A{EXPECTED_LINK_NUMBER}"
        assert module.module_number == EXPECTED_MODULE_NUMBER
        assert module.sw_version == "XP24_V0.34.03"
        assert module.hw_version == "XP24_HW_V1.00"
        assert module.auto_report_status == "ON"

    def test_datapoint_for_unknown_device_is_ignored(
        self, service: ConbusExportService, mock_telegram_service: Mock
    ) -> None:
        """Test a datapoint reply for an unknown device is ignored."""
        receive_datapoint(
            service,
            mock_telegram_service,
            SERIAL_A,
            DataPointType.MODULE_TYPE,
            "XP24",
        )

        assert service.device_configs == {}

    def test_invalid_datapoint_value_is_ignored(
        self, service: ConbusExportService, mock_telegram_service: Mock
    ) -> None:
        """Test a non-numeric value for a numeric datapoint is not stored."""
        receive_discovery(service, mock_telegram_service, SERIAL_A)

        receive_datapoint(
            service,
            mock_telegram_service,
            SERIAL_A,
            DataPointType.MODULE_TYPE_CODE,
            "XX",
        )

        assert service.device_configs[SERIAL_A].module_type_code == 0

    def test_complete_device_emits_exported_and_finishes(
        self,
        service: ConbusExportService,
        mock_telegram_service: Mock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test a fully answered device triggers export completion."""
        monkeypatch.chdir(tmp_path)
        exported_mock = Mock()
        finish_mock = Mock()
        service.on_device_exported.connect(exported_mock)
        service.on_finish.connect(finish_mock)

        receive_discovery(service, mock_telegram_service, SERIAL_A)
        complete_device(service, mock_telegram_service, SERIAL_A)

        exported_mock.assert_called_once_with(service.device_configs[SERIAL_A])
        finish_mock.assert_called_once_with(service.export_result)
        assert service.export_result.success is True
        assert service.export_result.export_status == "OK"
        assert service.export_result.device_count == 1
        assert service.export_result.output_file == "export.yml"
        assert service.export_result.config is not None
        assert (tmp_path / "export.yml").exists()

    def test_export_file_content_sorted_by_link_number(
        self,
        service: ConbusExportService,
        mock_telegram_service: Mock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test the export file lists modules sorted by link number."""
        monkeypatch.chdir(tmp_path)
        receive_discovery(service, mock_telegram_service, SERIAL_A)
        receive_discovery(service, mock_telegram_service, SERIAL_B)

        # SERIAL_A gets link 02, SERIAL_B gets link 01: B must be exported first.
        complete_device(service, mock_telegram_service, SERIAL_A)
        complete_device(
            service,
            mock_telegram_service,
            SERIAL_B,
            {**COMPLETE_DATAPOINTS, DataPointType.LINK_NUMBER: "01"},
        )

        modules = yaml.safe_load((tmp_path / "export.yml").read_text())
        assert len(modules) == DEVICE_COUNT_TWO
        assert [module["name"] for module in modules] == ["A1", "A2"]
        assert [module["serial_number"] for module in modules] == [SERIAL_B, SERIAL_A]
        # Internal fields must be excluded from the export
        for module in modules:
            assert "enabled" not in module
            assert "conbus_ip" not in module
            assert "conbus_port" not in module
            assert "action_table" not in module

    def test_timeout_with_incomplete_devices_finalizes_partial(
        self,
        service: ConbusExportService,
        mock_telegram_service: Mock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test timeout with incomplete devices produces a partial export."""
        monkeypatch.chdir(tmp_path)
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        receive_discovery(service, mock_telegram_service, SERIAL_A)

        service.timeout()

        finish_mock.assert_called_once_with(service.export_result)
        assert service.export_status == "FAILED_TIMEOUT"
        assert service.export_result.export_status == "FAILED_TIMEOUT"
        assert service.export_result.success is True
        assert (tmp_path / "export.yml").exists()

    def test_timeout_without_devices_fails(self, service: ConbusExportService) -> None:
        """Test timeout with no discovered devices reports failure."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.timeout()

        finish_mock.assert_called_once_with(service.export_result)
        assert service.export_result.success is False
        assert service.export_result.error == "No devices found"
        assert service.export_result.export_status == "FAILED_NO_DEVICES"

    def test_finalize_runs_only_once(self, service: ConbusExportService) -> None:
        """Test a second timeout does not emit on_finish again."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.timeout()
        service.timeout()

        finish_mock.assert_called_once()

    def test_write_failure_reports_failed_write(
        self,
        service: ConbusExportService,
        mock_telegram_service: Mock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test an unwritable output file reports FAILED_WRITE."""
        monkeypatch.chdir(tmp_path)
        # A directory named export.yml makes the file write fail
        (tmp_path / "export.yml").mkdir()
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        receive_discovery(service, mock_telegram_service, SERIAL_A)
        complete_device(service, mock_telegram_service, SERIAL_A)

        finish_mock.assert_called_once_with(service.export_result)
        assert service.export_result.success is False
        assert service.export_result.export_status == "FAILED_WRITE"
        assert service.export_result.error is not None

    def test_failed_emits_finish_with_error(self, service: ConbusExportService) -> None:
        """Test connection failure emits on_finish with error details."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.failed("Connection refused")

        finish_mock.assert_called_once_with(service.export_result)
        assert service.export_result.success is False
        assert service.export_result.error == "Connection refused"
        assert service.export_result.export_status == "FAILED_CONNECTION"

    def test_set_timeout(
        self, service: ConbusExportService, mock_conbus_protocol: Mock
    ) -> None:
        """Test set_timeout delegates to the protocol."""
        service.set_timeout(UPDATED_TIMEOUT_SECONDS)

        assert mock_conbus_protocol.timeout_seconds == UPDATED_TIMEOUT_SECONDS

    def test_set_event_loop(
        self, service: ConbusExportService, mock_conbus_protocol: Mock
    ) -> None:
        """Test set_event_loop delegates to the protocol."""
        event_loop = Mock()

        service.set_event_loop(event_loop)

        mock_conbus_protocol.set_event_loop.assert_called_once_with(event_loop)

    def test_start_reactor(
        self, service: ConbusExportService, mock_conbus_protocol: Mock
    ) -> None:
        """Test start_reactor delegates to the protocol."""
        service.start_reactor()

        mock_conbus_protocol.start_reactor.assert_called_once()

    def test_stop_reactor(
        self, service: ConbusExportService, mock_conbus_protocol: Mock
    ) -> None:
        """Test stop_reactor delegates to the protocol."""
        service.stop_reactor()

        mock_conbus_protocol.stop_reactor.assert_called_once()

    def test_context_manager_resets_and_disconnects(
        self,
        service: ConbusExportService,
        mock_conbus_protocol: Mock,
        mock_telegram_service: Mock,
    ) -> None:
        """Test context manager resets state and disconnects signals on exit."""
        receive_discovery(service, mock_telegram_service, SERIAL_A)
        service.export_status = "FAILED_TIMEOUT"

        with service as s:
            assert s is service
            # State must be reset for reuse
            assert s.discovered_devices == []
            assert s.device_configs == {}
            assert s.export_status == "OK"
            assert s.export_result.success is False

        mock_conbus_protocol.on_connection_made.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_sent.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_received.disconnect.assert_called_once()
        mock_conbus_protocol.on_timeout.disconnect.assert_called_once()
        mock_conbus_protocol.on_failed.disconnect.assert_called_once()
        mock_conbus_protocol.stop_reactor.assert_called_once()

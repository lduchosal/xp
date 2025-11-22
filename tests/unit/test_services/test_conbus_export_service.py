"""Unit tests for ConbusExportService."""

from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from xp.models.conbus.conbus_export import ConbusExportResponse
from xp.models.homekit.homekit_conson_config import ConsonModuleConfig
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.datapoint_type import DataPointType
from xp.services.conbus.conbus_export_service import ConbusExportService
from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol


class TestConbusExportService:
    """Unit tests for ConbusExportService functionality."""

    @pytest.fixture
    def mock_protocol(self):
        """Create a mock ConbusEventProtocol.

        Returns:
            Mock ConbusEventProtocol instance.
        """
        protocol = Mock(spec=ConbusEventProtocol)
        protocol.on_connection_made = Mock()
        protocol.on_telegram_sent = Mock()
        protocol.on_telegram_received = Mock()
        protocol.on_timeout = Mock()
        protocol.on_failed = Mock()
        protocol.on_connection_made.connect = Mock()
        protocol.on_telegram_sent.connect = Mock()
        protocol.on_telegram_received.connect = Mock()
        protocol.on_timeout.connect = Mock()
        protocol.on_failed.connect = Mock()
        protocol.on_connection_made.disconnect = Mock()
        protocol.on_telegram_sent.disconnect = Mock()
        protocol.on_telegram_received.disconnect = Mock()
        protocol.on_timeout.disconnect = Mock()
        protocol.on_failed.disconnect = Mock()
        protocol.send_telegram = Mock()
        protocol.timeout_seconds = 5
        protocol.start_reactor = Mock()
        protocol.stop_reactor = Mock()
        return protocol

    @pytest.fixture
    def service(self, mock_protocol):
        """Create service instance with mock protocol.

        Args:
            mock_protocol: Mock protocol fixture.

        Returns:
            ConbusExportService instance.
        """
        return ConbusExportService(conbus_protocol=mock_protocol)

    def test_service_initialization(self, service, mock_protocol):
        """Test service can be initialized with required dependencies."""
        assert service.export_result.success is False
        assert service.export_status == "OK"
        assert service.discovered_devices == []
        assert service.device_configs == {}
        assert service.device_datapoints_received == {}

        # Verify signal connections
        mock_protocol.on_connection_made.connect.assert_called_once()
        mock_protocol.on_telegram_sent.connect.assert_called_once()
        mock_protocol.on_telegram_received.connect.assert_called_once()
        mock_protocol.on_timeout.connect.assert_called_once()
        mock_protocol.on_failed.connect.assert_called_once()

    def test_datapoint_sequence_constant(self, service):
        """Test DATAPOINT_SEQUENCE has 7 datapoints."""
        assert len(service.DATAPOINT_SEQUENCE) == 7
        assert DataPointType.MODULE_TYPE in service.DATAPOINT_SEQUENCE
        assert DataPointType.MODULE_TYPE_CODE in service.DATAPOINT_SEQUENCE
        assert DataPointType.LINK_NUMBER in service.DATAPOINT_SEQUENCE
        assert DataPointType.MODULE_NUMBER in service.DATAPOINT_SEQUENCE
        assert DataPointType.SW_VERSION in service.DATAPOINT_SEQUENCE
        assert DataPointType.HW_VERSION in service.DATAPOINT_SEQUENCE
        assert DataPointType.AUTO_REPORT_STATUS in service.DATAPOINT_SEQUENCE

    def test_connection_made_sends_discovery(self, service, mock_protocol):
        """Test connection_made sends DISCOVERY telegram."""
        service.connection_made()

        mock_protocol.send_telegram.assert_called_once()
        call_kwargs = mock_protocol.send_telegram.call_args[1]
        assert call_kwargs["serial_number"] == "0000000000"

    def test_telegram_sent_records_telegram(self, service):
        """Test telegram_sent records sent telegram."""
        service.telegram_sent("<S0000000000F01D00FA>")

        assert service.export_result.sent_telegrams == ["<S0000000000F01D00FA>"]

    def test_telegram_received_records_telegram(self, service, mock_protocol):
        """Test telegram_received records received telegram."""
        event = TelegramReceivedEvent(
            protocol=mock_protocol,
            frame="<R1234567890F01D00AB>",
            telegram="R1234567890F01D00AB",
            payload="R1234567890F01D00",
            telegram_type="R",
            serial_number="1234567890",
            checksum="AB",
            checksum_valid=True,
        )

        service.telegram_received(event)

        assert service.export_result.received_telegrams == ["<R1234567890F01D00AB>"]

    def test_handle_discovery_response_adds_device(self, service, mock_protocol):
        """Test _handle_discovery_response adds device and sends queries."""
        event = TelegramReceivedEvent(
            protocol=mock_protocol,
            frame="<R1234567890F01D00AB>",
            telegram="R1234567890F01D00AB",
            payload="R1234567890F01D00",
            telegram_type="R",
            serial_number="1234567890",
            checksum="AB",
            checksum_valid=True,
        )

        service.telegram_received(event)

        # Verify device added
        assert "1234567890" in service.discovered_devices
        assert "1234567890" in service.device_configs
        assert service.device_configs["1234567890"]["serial_number"] == "1234567890"
        assert "1234567890" in service.device_datapoints_received

        # Verify 7 datapoint queries sent
        assert mock_protocol.send_telegram.call_count == 7

    def test_handle_discovery_response_ignores_duplicates(self, service, mock_protocol):
        """Test _handle_discovery_response ignores duplicate discoveries."""
        event = TelegramReceivedEvent(
            protocol=mock_protocol,
            frame="<R1234567890F01D00AB>",
            telegram="R1234567890F01D00AB",
            payload="R1234567890F01D00",
            telegram_type="R",
            serial_number="1234567890",
            checksum="AB",
            checksum_valid=True,
        )

        # First discovery
        service.telegram_received(event)
        first_count = mock_protocol.send_telegram.call_count

        # Duplicate discovery
        service.telegram_received(event)
        second_count = mock_protocol.send_telegram.call_count

        # Verify no additional queries sent
        assert second_count == first_count
        assert len(service.discovered_devices) == 1

    def test_handle_discovery_response_emits_progress(self, service, mock_protocol):
        """Test _handle_discovery_response emits progress signal."""
        progress_mock = Mock()
        service.on_progress.connect(progress_mock)

        event = TelegramReceivedEvent(
            protocol=mock_protocol,
            frame="<R1234567890F01D00AB>",
            telegram="R1234567890F01D00AB",
            payload="R1234567890F01D00",
            telegram_type="R",
            serial_number="1234567890",
            checksum="AB",
            checksum_valid=True,
        )

        service.telegram_received(event)

        progress_mock.assert_called_once_with("1234567890", 1, 1)

    def test_handle_datapoint_response_stores_module_type(self, service, mock_protocol):
        """Test _handle_datapoint_response stores MODULE_TYPE value."""
        # First discover device
        service._handle_discovery_response("1234567890")

        # Then receive MODULE_TYPE response (F02D00 = MODULE_TYPE)
        event = TelegramReceivedEvent(
            protocol=mock_protocol,
            frame="<R1234567890F02D00X130AB>",
            telegram="R1234567890F02D00X130AB",
            payload="R1234567890F02D00X130",
            telegram_type="R",
            serial_number="1234567890",
            checksum="AB",
            checksum_valid=True,
        )

        service.telegram_received(event)

        assert service.device_configs["1234567890"]["module_type"] == "X130"

    def test_handle_datapoint_response_stores_module_type_code(
        self, service, mock_protocol
    ):
        """Test _handle_datapoint_response stores MODULE_TYPE_CODE value."""
        service._handle_discovery_response("1234567890")

        # F02D07 = MODULE_TYPE_CODE
        event = TelegramReceivedEvent(
            protocol=mock_protocol,
            frame="<R1234567890F02D0713AB>",
            telegram="R1234567890F02D0713AB",
            payload="R1234567890F02D0713",
            telegram_type="R",
            serial_number="1234567890",
            checksum="AB",
            checksum_valid=True,
        )

        service.telegram_received(event)

        assert service.device_configs["1234567890"]["module_type_code"] == 13

    def test_handle_datapoint_response_stores_link_number(self, service, mock_protocol):
        """Test _handle_datapoint_response stores LINK_NUMBER value."""
        service._handle_discovery_response("1234567890")

        # F02D04 = LINK_NUMBER
        event = TelegramReceivedEvent(
            protocol=mock_protocol,
            frame="<R1234567890F02D0412AB>",
            telegram="R1234567890F02D0412AB",
            payload="R1234567890F02D0412",
            telegram_type="R",
            serial_number="1234567890",
            checksum="AB",
            checksum_valid=True,
        )

        service.telegram_received(event)

        assert service.device_configs["1234567890"]["link_number"] == 12

    def test_handle_datapoint_response_stores_all_fields(self, service, mock_protocol):
        """Test _handle_datapoint_response stores all 7 datapoint values."""
        service._handle_discovery_response("1234567890")

        # Send all 7 datapoint responses
        datapoints = [
            ("00", "X130"),  # MODULE_TYPE
            ("07", "13"),  # MODULE_TYPE_CODE
            ("04", "12"),  # LINK_NUMBER
            ("05", "01"),  # MODULE_NUMBER
            ("02", "V1"),  # SW_VERSION
            ("01", "HA"),  # HW_VERSION
            ("21", "AA"),  # AUTO_REPORT_STATUS
        ]

        for dp_code, value in datapoints:
            event = TelegramReceivedEvent(
                protocol=mock_protocol,
                frame=f"<R1234567890F02D{dp_code}{value}AB>",
                telegram=f"R1234567890F02D{dp_code}{value}AB",
                payload=f"R1234567890F02D{dp_code}{value}",
                telegram_type="R",
                serial_number="1234567890",
                checksum="AB",
                checksum_valid=True,
            )
            service.telegram_received(event)

        config = service.device_configs["1234567890"]
        assert config["module_type"] == "X130"
        assert config["module_type_code"] == 13
        assert config["link_number"] == 12
        assert config["module_number"] == 1
        assert config["sw_version"] == "V1"
        assert config["hw_version"] == "HA"
        assert config["auto_report_status"] == "AA"

    def test_check_device_complete_emits_signal(self, service, mock_protocol):
        """Test _check_device_complete emits on_device_exported when all datapoints received."""
        device_exported_mock = Mock()
        service.on_device_exported.connect(device_exported_mock)

        service._handle_discovery_response("1234567890")

        # Send all 7 datapoints
        for dp in service.DATAPOINT_SEQUENCE:
            service._store_datapoint_value("1234567890", dp, "XX")
            service.device_datapoints_received["1234567890"].add(dp.value)

        service._check_device_complete("1234567890")

        # Verify signal emitted
        device_exported_mock.assert_called_once()
        emitted_config = device_exported_mock.call_args[0][0]
        assert isinstance(emitted_config, ConsonModuleConfig)
        assert emitted_config.serial_number == "1234567890"

    def test_finalize_export_no_devices(self, service):
        """Test _finalize_export handles no devices found."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service._finalize_export()

        assert service.export_status == "FAILED_NO_DEVICES"
        assert service.export_result.success is False
        assert service.export_result.error == "No devices found"
        finish_mock.assert_called_once()

    @patch("builtins.open", new_callable=mock_open)
    @patch("xp.services.conbus.conbus_export_service.yaml")
    def test_finalize_export_writes_file(self, _mock_yaml_module, mock_file, service):
        """Test _finalize_export writes export.yml file."""
        # Add a complete device
        service._handle_discovery_response("1234567890")
        for dp in service.DATAPOINT_SEQUENCE:
            service._store_datapoint_value("1234567890", dp, "XX")
            service.device_datapoints_received["1234567890"].add(dp.value)

        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service._finalize_export()

        # Verify file written
        mock_file.assert_called_once_with(Path("export.yml"), "w")
        assert service.export_result.success is True
        assert service.export_result.export_status == "OK"

    def test_timeout_partial_export(self, service, mock_protocol):
        """Test timeout creates partial export with incomplete devices."""
        # Add device with only partial datapoints
        service._handle_discovery_response("1234567890")
        service._store_datapoint_value("1234567890", DataPointType.MODULE_TYPE, "X130")
        service.device_datapoints_received["1234567890"].add(
            DataPointType.MODULE_TYPE.value
        )

        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        with patch("builtins.open", new_callable=mock_open):
            with patch("xp.services.conbus.conbus_export_service.yaml"):
                service.timeout()

        assert service.export_status == "FAILED_TIMEOUT"

    def test_timeout_all_complete(self, service, mock_protocol):
        """Test timeout with all devices complete sets status OK."""
        # Add complete device
        service._handle_discovery_response("1234567890")
        for dp in service.DATAPOINT_SEQUENCE:
            service._store_datapoint_value("1234567890", dp, "XX")
            service.device_datapoints_received["1234567890"].add(dp.value)

        with patch("builtins.open", new_callable=mock_open):
            with patch("xp.services.conbus.conbus_export_service.yaml"):
                service.timeout()

        assert service.export_status == "OK"

    def test_failed_sets_connection_error(self, service):
        """Test failed callback sets FAILED_CONNECTION status."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.failed("Connection timeout")

        assert service.export_status == "FAILED_CONNECTION"
        assert service.export_result.success is False
        assert service.export_result.error == "Connection timeout"
        assert service.export_result.export_status == "FAILED_CONNECTION"
        finish_mock.assert_called_once()

    def test_set_timeout(self, service, mock_protocol):
        """Test set_timeout method sets timeout on protocol."""
        service.set_timeout(timeout_seconds=10)

        assert mock_protocol.timeout_seconds == 10

    def test_start_reactor(self, service, mock_protocol):
        """Test start_reactor delegates to protocol."""
        service.start_reactor()

        mock_protocol.start_reactor.assert_called_once()

    def test_stop_reactor(self, service, mock_protocol):
        """Test stop_reactor delegates to protocol."""
        service.stop_reactor()

        mock_protocol.stop_reactor.assert_called_once()

    def test_context_manager_enter(self, service):
        """Test __enter__ resets state and returns self."""
        # Modify state
        service.discovered_devices = ["1234567890"]
        service.device_configs = {"1234567890": {}}
        service.export_status = "FAILED"

        # Enter context
        result = service.__enter__()

        # Verify state reset
        assert result is service
        assert service.discovered_devices == []
        assert service.device_configs == {}
        assert service.device_datapoints_received == {}
        assert service.export_status == "OK"

    def test_context_manager_exit(self, service, mock_protocol):
        """Test __exit__ disconnects all signals."""
        service.__exit__(None, None, None)

        # Verify all signals disconnected
        mock_protocol.on_connection_made.disconnect.assert_called_once()
        mock_protocol.on_telegram_sent.disconnect.assert_called_once()
        mock_protocol.on_telegram_received.disconnect.assert_called_once()
        mock_protocol.on_timeout.disconnect.assert_called_once()
        mock_protocol.on_failed.disconnect.assert_called_once()
        mock_protocol.stop_reactor.assert_called_once()

    def test_signal_connections(self, service):
        """Test signals can be connected and emit correctly."""
        progress_mock = Mock()
        device_exported_mock = Mock()
        finish_mock = Mock()

        # Connect signals
        service.on_progress.connect(progress_mock)
        service.on_device_exported.connect(device_exported_mock)
        service.on_finish.connect(finish_mock)

        # Emit signals
        service.on_progress.emit("1234567890", 1, 1)
        service.on_finish.emit(service.export_result)

        # Verify callbacks called
        progress_mock.assert_called_once_with("1234567890", 1, 1)
        finish_mock.assert_called_once_with(service.export_result)

    def test_handle_datapoint_response_unknown_device(self, service, mock_protocol):
        """Test _handle_datapoint_response ignores unknown devices."""
        # Send datapoint response without discovery
        event = TelegramReceivedEvent(
            protocol=mock_protocol,
            frame="<R9999999999F02D00X130AB>",
            telegram="R9999999999F02D00X130AB",
            payload="R9999999999F02D00X130",
            telegram_type="R",
            serial_number="9999999999",
            checksum="AB",
            checksum_valid=True,
        )

        # Should not crash
        service.telegram_received(event)

        # Verify device not added
        assert "9999999999" not in service.device_configs

    def test_handle_datapoint_response_invalid_code(self, service, mock_protocol):
        """Test _handle_datapoint_response handles invalid datapoint codes."""
        service._handle_discovery_response("1234567890")

        # Send invalid datapoint code
        event = TelegramReceivedEvent(
            protocol=mock_protocol,
            frame="<R1234567890F02D99XXAB>",
            telegram="R1234567890F02D99XXAB",
            payload="R1234567890F02D99XX",
            telegram_type="R",
            serial_number="1234567890",
            checksum="AB",
            checksum_valid=True,
        )

        # Should not crash
        service.telegram_received(event)

    def test_store_datapoint_value_invalid_number(self, service):
        """Test _store_datapoint_value handles invalid number values."""
        service._handle_discovery_response("1234567890")

        # Store invalid link_number
        service._store_datapoint_value("1234567890", DataPointType.LINK_NUMBER, "XX")

        # Verify no exception raised and value not stored
        assert "link_number" not in service.device_configs["1234567890"]


class TestConbusExportResponseModel:
    """Unit tests for ConbusExportResponse model."""

    def test_default_values(self):
        """Test ConbusExportResponse default field values."""
        response = ConbusExportResponse(success=True)

        assert response.success is True
        assert response.config is None
        assert response.device_count == 0
        assert response.output_file == "export.yml"
        assert response.export_status == "OK"
        assert response.error is None
        assert response.sent_telegrams == []
        assert response.received_telegrams == []

    def test_custom_values(self):
        """Test ConbusExportResponse with custom values."""
        response = ConbusExportResponse(
            success=False,
            device_count=3,
            output_file="custom.yml",
            export_status="FAILED_TIMEOUT",
            error="Timeout occurred",
            sent_telegrams=["<S1>", "<S2>"],
            received_telegrams=["<R1>", "<R2>", "<R3>"],
        )

        assert response.success is False
        assert response.device_count == 3
        assert response.output_file == "custom.yml"
        assert response.export_status == "FAILED_TIMEOUT"
        assert response.error == "Timeout occurred"
        assert len(response.sent_telegrams) == 2
        assert len(response.received_telegrams) == 3

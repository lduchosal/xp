"""Unit tests for MsActionTableUploadService."""

from unittest.mock import Mock, patch

import pytest

from xp.models.actiontable.msactiontable_xp20 import Xp20MsActionTable
from xp.models.actiontable.msactiontable_xp24 import Xp24MsActionTable
from xp.models.actiontable.msactiontable_xp33 import Xp33MsActionTable
from xp.models.config.conson_module_config import ConsonModuleConfig
from xp.models.protocol.conbus_protocol import TelegramReceivedEvent
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.telegram_type import TelegramType
from xp.services.conbus.msactiontable.msactiontable_upload_service import (
    MsActionTableUploadError,
    MsActionTableUploadService,
)


class TestMsActionTableUploadService:
    """Test cases for MsActionTableUploadService."""

    @pytest.fixture
    def mock_conbus_protocol(self):
        """Create mock ConbusEventProtocol."""
        from xp.services.protocol.conbus_event_protocol import ConbusEventProtocol

        protocol = Mock(spec=ConbusEventProtocol)
        protocol.on_connection_made = Mock()
        protocol.on_connection_made.connect = Mock()
        protocol.on_connection_made.disconnect = Mock()
        protocol.on_telegram_sent = Mock()
        protocol.on_telegram_sent.connect = Mock()
        protocol.on_telegram_sent.disconnect = Mock()
        protocol.on_telegram_received = Mock()
        protocol.on_telegram_received.connect = Mock()
        protocol.on_telegram_received.disconnect = Mock()
        protocol.on_timeout = Mock()
        protocol.on_timeout.connect = Mock()
        protocol.on_timeout.disconnect = Mock()
        protocol.on_failed = Mock()
        protocol.on_failed.connect = Mock()
        protocol.on_failed.disconnect = Mock()
        protocol.send_telegram = Mock()
        protocol.start_reactor = Mock()
        protocol.stop_reactor = Mock()
        protocol.timeout_seconds = 5.0
        return protocol

    @pytest.fixture
    def mock_xp20_serializer(self):
        """Create mock XP20 serializer."""
        return Mock()

    @pytest.fixture
    def mock_xp24_serializer(self):
        """Create mock XP24 serializer."""
        return Mock()

    @pytest.fixture
    def mock_xp33_serializer(self):
        """Create mock XP33 serializer."""
        return Mock()

    @pytest.fixture
    def mock_telegram_service(self):
        """Create mock TelegramService."""
        return Mock()

    @pytest.fixture
    def mock_conson_config(self):
        """Create mock Conson config."""
        return Mock()

    @pytest.fixture
    def service(
        self,
        mock_conbus_protocol,
        mock_xp20_serializer,
        mock_xp24_serializer,
        mock_xp33_serializer,
        mock_telegram_service,
        mock_conson_config,
    ):
        """Create service instance for testing."""
        return MsActionTableUploadService(
            conbus_protocol=mock_conbus_protocol,
            xp20ms_serializer=mock_xp20_serializer,
            xp24ms_serializer=mock_xp24_serializer,
            xp33ms_serializer=mock_xp33_serializer,
            telegram_service=mock_telegram_service,
            conson_config=mock_conson_config,
        )

    def test_service_initialization(
        self,
        mock_conbus_protocol,
        mock_xp20_serializer,
        mock_xp24_serializer,
        mock_xp33_serializer,
        mock_telegram_service,
        mock_conson_config,
    ):
        """Test service can be initialized with required dependencies."""
        service = MsActionTableUploadService(
            conbus_protocol=mock_conbus_protocol,
            xp20ms_serializer=mock_xp20_serializer,
            xp24ms_serializer=mock_xp24_serializer,
            xp33ms_serializer=mock_xp33_serializer,
            telegram_service=mock_telegram_service,
            conson_config=mock_conson_config,
        )

        assert service.conbus_protocol == mock_conbus_protocol
        assert service.xp20ms_serializer == mock_xp20_serializer
        assert service.xp24ms_serializer == mock_xp24_serializer
        assert service.xp33ms_serializer == mock_xp33_serializer
        assert service.telegram_service == mock_telegram_service
        assert service.conson_config == mock_conson_config
        assert service.serial_number == ""
        assert service.xpmoduletype == ""
        assert hasattr(service, "on_progress")
        assert hasattr(service, "on_error")
        assert hasattr(service, "on_finish")
        assert service.upload_data == ""
        assert service.upload_initiated is False

        # Verify signals were connected
        mock_conbus_protocol.on_connection_made.connect.assert_called_once()
        mock_conbus_protocol.on_telegram_sent.connect.assert_called_once()
        mock_conbus_protocol.on_telegram_received.connect.assert_called_once()
        mock_conbus_protocol.on_timeout.connect.assert_called_once()
        mock_conbus_protocol.on_failed.connect.assert_called_once()

    def test_connection_made(self, service, mock_conbus_protocol):
        """Test connection_made sends UPLOAD_MSACTIONTABLE telegram."""
        service.serial_number = "0020044991"

        service.connection_made()

        mock_conbus_protocol.send_telegram.assert_called_once_with(
            telegram_type=TelegramType.SYSTEM,
            serial_number="0020044991",
            system_function=SystemFunction.UPLOAD_MSACTIONTABLE,
            data_value="00",
        )

    def test_upload_xp24_msactiontable_success(
        self, service, mock_conson_config, mock_xp24_serializer, mock_conbus_protocol
    ):
        """Test successful XP24 msactiontable upload."""
        # Setup module config
        module = Mock(spec=ConsonModuleConfig)
        module.module_type = "XP24"
        module.xp24_msaction_table = [
            "T:1 T:2 ON:0 OF:0 | M12:0 M34:0 C12:0 C34:0 DT:12"
        ]
        mock_conson_config.find_module.return_value = module

        # Setup serializer
        mock_msactiontable = Mock(spec=Xp24MsActionTable)
        mock_xp24_serializer.to_data.return_value = "AAAA" + "A" * 64  # 68 chars total

        # Mock from_short_format
        with patch(
            "xp.models.actiontable.msactiontable_xp24.Xp24MsActionTable.from_short_format",
            return_value=mock_msactiontable,
        ):
            service.start(
                serial_number="0020044991",
                xpmoduletype="xp24",
            )

        assert service.serial_number == "0020044991"
        assert service.xpmoduletype == "xp24"
        assert service.upload_data == "AAAA" + "A" * 64
        assert service.serializer == mock_xp24_serializer

    def test_upload_xp20_msactiontable_success(
        self, service, mock_conson_config, mock_xp20_serializer
    ):
        """Test successful XP20 msactiontable upload."""
        # Setup module config
        module = Mock(spec=ConsonModuleConfig)
        module.module_type = "XP20"
        module.xp20_msaction_table = [
            "T:1 T:2 ON:0 OF:0 | M12:0 M34:0 C12:0 C34:0 DT:12"
        ]
        mock_conson_config.find_module.return_value = module

        # Setup serializer
        mock_msactiontable = Mock(spec=Xp20MsActionTable)
        mock_xp20_serializer.to_data.return_value = "AAAA" + "A" * 64

        # Mock from_short_format
        with patch(
            "xp.models.actiontable.msactiontable_xp20.Xp20MsActionTable.from_short_format",
            return_value=mock_msactiontable,
        ):
            service.start(
                serial_number="0020044991",
                xpmoduletype="xp20",
            )

        assert service.xpmoduletype == "xp20"
        assert service.serializer == mock_xp20_serializer

    def test_upload_xp33_msactiontable_success(
        self, service, mock_conson_config, mock_xp33_serializer
    ):
        """Test successful XP33 msactiontable upload."""
        # Setup module config
        module = Mock(spec=ConsonModuleConfig)
        module.module_type = "XP33"
        module.xp33_msaction_table = [
            "T:1 T:2 ON:0 OF:0 | M12:0 M34:0 C12:0 C34:0 DT:12"
        ]
        mock_conson_config.find_module.return_value = module

        # Setup serializer
        mock_msactiontable = Mock(spec=Xp33MsActionTable)
        mock_xp33_serializer.to_data.return_value = "AAAA" + "A" * 64

        # Mock from_short_format
        with patch(
            "xp.models.actiontable.msactiontable_xp33.Xp33MsActionTable.from_short_format",
            return_value=mock_msactiontable,
        ):
            service.start(
                serial_number="0020044991",
                xpmoduletype="xp33",
            )

        assert service.xpmoduletype == "xp33"
        assert service.serializer == mock_xp33_serializer

    def test_upload_module_not_found(self, service, mock_conson_config):
        """Test error when module not found in config."""
        mock_conson_config.find_module.return_value = None

        error_emitted: list[str] = []
        service.on_error.connect(error_emitted.append)

        service.start(
            serial_number="0020044991",
            xpmoduletype="xp24",
        )

        assert len(error_emitted) == 1
        assert "not found in conson.yml" in error_emitted[0]

    def test_upload_module_type_mismatch(self, service, mock_conson_config):
        """Test error when module type doesn't match argument."""
        module = Mock(spec=ConsonModuleConfig)
        module.module_type = "XP20"
        mock_conson_config.find_module.return_value = module

        error_emitted: list[str] = []
        service.on_error.connect(error_emitted.append)

        service.start(
            serial_number="0020044991",
            xpmoduletype="xp24",
        )

        assert len(error_emitted) == 1
        assert "Module type mismatch" in error_emitted[0]

    def test_upload_missing_msactiontable_config(self, service, mock_conson_config):
        """Test error when msactiontable field is missing."""
        module = Mock(spec=ConsonModuleConfig)
        module.module_type = "XP24"
        module.xp24_msaction_table = None
        mock_conson_config.find_module.return_value = module

        error_emitted: list[str] = []
        service.on_error.connect(error_emitted.append)

        service.start(
            serial_number="0020044991",
            xpmoduletype="xp24",
        )

        assert len(error_emitted) == 1
        assert "does not have xp24_msaction_table configured" in error_emitted[0]

    def test_upload_empty_msactiontable_list(self, service, mock_conson_config):
        """Test error when msactiontable list is empty."""
        module = Mock(spec=ConsonModuleConfig)
        module.module_type = "XP24"
        module.xp24_msaction_table = []
        mock_conson_config.find_module.return_value = module

        error_emitted: list[str] = []
        service.on_error.connect(error_emitted.append)

        service.start(
            serial_number="0020044991",
            xpmoduletype="xp24",
        )

        assert len(error_emitted) == 1
        # Empty list is treated same as None in getattr check
        assert (
            "does not have xp24_msaction_table configured" in error_emitted[0]
            or "empty xp24_msaction_table list" in error_emitted[0]
        )

    def test_upload_invalid_short_format(self, service, mock_conson_config):
        """Test error when short format is invalid."""
        module = Mock(spec=ConsonModuleConfig)
        module.module_type = "XP24"
        module.xp24_msaction_table = ["invalid format"]
        mock_conson_config.find_module.return_value = module

        error_emitted: list[str] = []
        service.on_error.connect(error_emitted.append)

        with patch(
            "xp.models.actiontable.msactiontable_xp24.Xp24MsActionTable.from_short_format",
            side_effect=ValueError("Invalid format"),
        ):
            service.start(
                serial_number="0020044991",
                xpmoduletype="xp24",
            )

        assert len(error_emitted) == 1
        assert "Invalid msactiontable format" in error_emitted[0]

    def test_upload_unsupported_module_type(self, service):
        """Test error when unsupported module type is provided."""
        with pytest.raises(MsActionTableUploadError) as exc_info:
            service.start(
                serial_number="0020044991",
                xpmoduletype="xp99",
            )

        assert "Unsupported module type: xp99" in str(exc_info.value)

    def test_handle_ack_sends_data(
        self, service, mock_conbus_protocol, mock_telegram_service
    ):
        """Test that first ACK triggers data send."""
        service.serial_number = "0020044991"
        service.upload_data = "AAAA" + "A" * 64
        service.upload_initiated = False

        # Create ACK telegram
        ack_telegram = ReplyTelegram(
            checksum="XX",
            raw_telegram="<R0020044991F18D00XX>",
            system_function=SystemFunction.ACK,
            data="",
            data_value="00",
        )
        mock_telegram_service.parse_reply_telegram.return_value = ack_telegram

        # Simulate telegram received
        telegram_event = TelegramReceivedEvent(
            protocol=mock_conbus_protocol,
            frame="<R0020044991F18D00XX>",
            telegram="R0020044991F18D00XX",
            payload="R0020044991F18D00",
            telegram_type=TelegramType.REPLY.value,
            serial_number="0020044991",
            checksum="XX",
            checksum_valid=True,
        )

        progress_emitted: list[str] = []
        service.on_progress.connect(progress_emitted.append)

        service.telegram_received(telegram_event)

        # Should send data chunk
        assert mock_conbus_protocol.send_telegram.call_count == 1
        call_args = mock_conbus_protocol.send_telegram.call_args
        assert call_args[1]["system_function"] == SystemFunction.MSACTIONTABLE
        assert call_args[1]["data_value"] == "AAAA" + "A" * 64
        assert service.upload_initiated is True
        assert len(progress_emitted) == 1

    def test_handle_ack_sends_eof(
        self, service, mock_conbus_protocol, mock_telegram_service
    ):
        """Test that second ACK triggers EOF send."""
        service.serial_number = "0020044991"
        service.upload_data = "AAAA" + "A" * 64
        service.upload_initiated = True

        # Create ACK telegram
        ack_telegram = ReplyTelegram(
            checksum="XX",
            raw_telegram="<R0020044991F18D00XX>",
            system_function=SystemFunction.ACK,
            data="",
            data_value="00",
        )
        mock_telegram_service.parse_reply_telegram.return_value = ack_telegram

        # Simulate telegram received
        telegram_event = TelegramReceivedEvent(
            protocol=mock_conbus_protocol,
            frame="<R0020044991F18D00XX>",
            telegram="R0020044991F18D00XX",
            payload="R0020044991F18D00",
            telegram_type=TelegramType.REPLY.value,
            serial_number="0020044991",
            checksum="XX",
            checksum_valid=True,
        )

        finish_emitted: list[str] = []
        service.on_finish.connect(finish_emitted.append)

        service.telegram_received(telegram_event)

        # Should send EOF
        assert mock_conbus_protocol.send_telegram.call_count == 1
        call_args = mock_conbus_protocol.send_telegram.call_args
        assert call_args[1]["system_function"] == SystemFunction.EOF
        assert len(finish_emitted) == 1
        assert finish_emitted[0] is True

    def test_handle_nak_response(
        self, service, mock_telegram_service, mock_conbus_protocol
    ):
        """Test NAK response triggers error."""
        service.serial_number = "0020044991"

        # Create NAK telegram
        nak_telegram = ReplyTelegram(
            checksum="XX",
            raw_telegram="<R0020044991F19D00XX>",
            system_function=SystemFunction.NAK,
            data="",
            data_value="00",
        )
        mock_telegram_service.parse_reply_telegram.return_value = nak_telegram

        # Simulate telegram received
        telegram_event = TelegramReceivedEvent(
            protocol=mock_conbus_protocol,
            frame="<R0020044991F19D00XX>",
            telegram="R0020044991F19D00XX",
            payload="R0020044991F19D00",
            telegram_type=TelegramType.REPLY.value,
            serial_number="0020044991",
            checksum="XX",
            checksum_valid=True,
        )

        error_emitted: list[str] = []
        service.on_error.connect(error_emitted.append)

        service.telegram_received(telegram_event)

        assert len(error_emitted) == 1
        assert "NAK received" in error_emitted[0]

    def test_timeout_triggers_error(self, service):
        """Test timeout triggers error signal."""
        error_emitted: list[str] = []
        service.on_error.connect(error_emitted.append)

        service.timeout()

        assert len(error_emitted) == 1
        assert "timeout" in error_emitted[0].lower()

    def test_context_manager_resets_state(self, service):
        """Test context manager resets state on entry."""
        service.upload_data = "test_data"
        service.upload_initiated = True
        service.serial_number = "0020044991"
        service.xpmoduletype = "xp24"

        with service as svc:
            assert svc.upload_data == ""
            assert svc.upload_initiated is False
            assert svc.serial_number == ""
            assert svc.xpmoduletype == ""

    def test_context_manager_disconnects_signals(self, service, mock_conbus_protocol):
        """Test context manager disconnects signals on exit."""
        with service:
            pass

        # Verify protocol signals were disconnected
        mock_conbus_protocol.on_connection_made.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_sent.disconnect.assert_called_once()
        mock_conbus_protocol.on_telegram_received.disconnect.assert_called_once()
        mock_conbus_protocol.on_timeout.disconnect.assert_called_once()
        mock_conbus_protocol.on_failed.disconnect.assert_called_once()
        # Verify reactor was stopped
        mock_conbus_protocol.stop_reactor.assert_called_once()

    def test_set_timeout(self, service, mock_conbus_protocol):
        """Test set_timeout configures protocol timeout."""
        service.set_timeout(10.0)
        assert mock_conbus_protocol.timeout_seconds == 10.0

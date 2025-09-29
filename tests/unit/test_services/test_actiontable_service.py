"""Unit tests for ActionTableService."""

import pytest
from unittest.mock import Mock, patch

from xp.services.actiontable_service import ActionTableService, ActionTableError
from xp.models.actiontable import ActionTable, ActionTableEntry
from xp.models import ModuleTypeCode
from xp.models.input_action_type import InputActionType
from xp.models.timeparam_type import TimeParam


class TestActionTableService:
    """Test cases for ActionTableService"""

    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        with patch("xp.services.actiontable_service.ConbusService"):
            with patch("xp.services.actiontable_service.TelegramService"):
                return ActionTableService()

    @pytest.fixture
    def sample_actiontable(self):
        """Create sample ActionTable for testing"""
        entries = [
            ActionTableEntry(
                module_type=ModuleTypeCode.CP20,
                link_number=0,
                module_input=0,
                module_output=1,
                inverted=False,
                command=InputActionType.TURNOFF,
                parameter=TimeParam.NONE,
            ),
            ActionTableEntry(
                module_type=ModuleTypeCode.CP20,
                link_number=0,
                module_input=1,
                module_output=1,
                inverted=True,
                command=InputActionType.TURNON,
                parameter=TimeParam.NONE,
            ),
        ]
        return ActionTable(entries=entries)

    def test_format_decoded_output(self, service, sample_actiontable):
        """Test formatting ActionTable as decoded output"""
        result = service.format_decoded_output(sample_actiontable)

        expected_lines = ["CP20 0 0 > 1 TURNOFF;", "CP20 0 1 > 1 ~TURNON;"]

        assert result == "\n".join(expected_lines)

    def test_format_encoded_output(self, service, sample_actiontable):
        """Test formatting ActionTable as encoded output"""
        result = service.format_encoded_output(sample_actiontable)

        # Should return a base64-like encoded string
        assert isinstance(result, str)
        assert len(result) > 0

    @patch("xp.services.actiontable_service.ConbusService")
    @patch("xp.services.actiontable_service.TelegramService")
    def test_download_actiontable_success(
        self, mock_telegram_service, mock_conbus_service
    ):
        """Test successful actiontable download"""
        from xp.models.system_function import SystemFunction

        # Setup mocks
        mock_conbus = Mock()
        mock_conbus_service.return_value = mock_conbus

        mock_telegram = Mock()
        mock_telegram_service.return_value = mock_telegram

        service = ActionTableService()

        # Mock calls to simulate the communication flow
        call_count = [0]

        def mock_send_telegram(_serial, _function, _data, callback):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: simulate receiving actiontable data
                mock_actiontable_reply = Mock()
                mock_actiontable_reply.system_function = SystemFunction.ACTIONTABLE
                mock_actiontable_reply.raw_telegram = "AAAAACAAAABAAAAC"
                mock_actiontable_reply.data_value = (
                    "XXAAAAACAAAABAAAAC"  # Add data_value for slicing
                )
                mock_telegram.parse_reply_telegram.return_value = mock_actiontable_reply
                callback(["<R0123450001F17DAAAAACAAAABAAAAC>"])
            elif call_count[0] == 2:
                # Second call: simulate receiving EOF
                mock_eof_reply = Mock()
                mock_eof_reply.system_function = SystemFunction.EOF
                mock_eof_reply.raw_telegram = "<R0123450001F16DEO>"
                mock_telegram.parse_reply_telegram.return_value = mock_eof_reply
                callback(["<R0123450001F16DEO>"])

        mock_conbus.send_telegram.side_effect = mock_send_telegram

        # Mock receive_responses to not interfere
        mock_conbus.receive_responses.return_value = None

        # Mock serializer to return a valid ActionTable
        with patch.object(
            service.serializer, "from_encoded_string"
        ) as mock_deserialize:
            mock_deserialize.return_value = ActionTable(entries=[])

            # Test the download
            result = service.download_actiontable("012345")

            assert isinstance(result, ActionTable)
            assert mock_conbus.send_telegram.called

    def test_download_actiontable_communication_error(self, service):
        """Test actiontable download with communication error"""
        with patch.object(service.conbus_service, "send_telegram") as mock_send:
            mock_send.side_effect = Exception("Connection failed")

            with pytest.raises(ActionTableError) as exc_info:
                service.download_actiontable("012345")

            assert "communication failed" in str(exc_info.value).lower()

    def test_is_eof_true(self, service):
        """Test _is_eof returns True for EOF telegrams"""
        from xp.models.system_function import SystemFunction

        mock_reply = Mock()
        mock_reply.system_function = SystemFunction.EOF

        with patch.object(
            service.telegram_service, "parse_reply_telegram", return_value=mock_reply
        ):
            result = service._is_eof(["<R0123450001F16DFO>"])
            assert result is True

    def test_is_eof_false(self, service):
        """Test _is_eof returns False for non-EOF telegrams"""
        from xp.models.system_function import SystemFunction

        mock_reply = Mock()
        mock_reply.system_function = SystemFunction.ACK

        with patch.object(
            service.telegram_service, "parse_reply_telegram", return_value=mock_reply
        ):
            result = service._is_eof(["<R0123450001F18DFA>"])
            assert result is False

    def test_get_actiontable_data_found(self, service):
        """Test _get_actiontable_data extracts data successfully"""
        from xp.models.system_function import SystemFunction

        mock_reply = Mock()
        mock_reply.system_function = SystemFunction.ACTIONTABLE
        mock_reply.raw_telegram = "<R0123450001F17DAAAAACAAAABAAAACFK>"
        mock_reply.data_value = "XXAAAAACAAAABAAAAC"  # Add data_value for slicing

        with patch.object(
            service.telegram_service, "parse_reply_telegram", return_value=mock_reply
        ):
            result = service._get_actiontable_data(
                ["<R0123450001F17DAAAAACAAAABAAAACFK>"]
            )
            assert result is not None
            assert isinstance(result, str)

    def test_get_actiontable_data_not_found(self, service):
        """Test _get_actiontable_data returns None when no data found"""
        from xp.models.system_function import SystemFunction

        mock_reply = Mock()
        mock_reply.system_function = SystemFunction.ACK

        with patch.object(
            service.telegram_service, "parse_reply_telegram", return_value=mock_reply
        ):
            result = service._get_actiontable_data(["<R0123450001F18DFA>"])
            assert result is None

    def test_context_manager(self, service):
        """Test service works as context manager"""
        with service as ctx_service:
            assert ctx_service is service

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from xp.services.conbus_linknumber_service import ConbusLinknumberService
from xp.services.telegram_link_number_service import LinkNumberError
from xp.models.conbus_linknumber import ConbusLinknumberResponse
from xp.models.reply_telegram import ReplyTelegram


class TestConbusLinknumberService:
    """Test cases for ConbusLinknumberService"""

    @pytest.fixture
    def mock_config_file(self, tmp_path):
        """Create a temporary config file for testing"""
        config_file = tmp_path / "test_cli.yml"
        config_content = """
conbus:
  ip: 10.0.0.1
  port: 8080
  timeout: 15
"""
        config_file.write_text(config_content)
        return str(config_file)

    @pytest.fixture
    def service(self, mock_config_file):
        """Create service instance with test config"""
        return ConbusLinknumberService(config_path=mock_config_file)

    def test_service_initialization(self, mock_config_file):
        """Test service initialization"""
        service = ConbusLinknumberService(config_path=mock_config_file)

        assert service.conbus_service is not None
        assert service.datapoint_service is not None
        assert service.link_number_service is not None
        assert service.telegram_service is not None

    @patch("xp.services.conbus_linknumber_service.ConbusService")
    @patch("xp.services.conbus_linknumber_service.LinkNumberService")
    @patch("xp.services.conbus_linknumber_service.TelegramService")
    def test_set_linknumber_success_ack(
        self,
        mock_telegram_service_class,
        mock_link_service_class,
        mock_conbus_service_class,
    ):
        """Test successful link number setting with ACK response"""
        # Setup mocks
        mock_conbus_service = Mock()
        mock_conbus_service.__enter__ = Mock(return_value=mock_conbus_service)
        mock_conbus_service.__exit__ = Mock(return_value=None)
        mock_conbus_service_class.return_value = mock_conbus_service

        mock_link_service = Mock()
        mock_link_service_class.return_value = mock_link_service
        mock_link_service.generate_set_link_number_telegram.return_value = (
            "<S0123450001F04D0425FO>"
        )
        mock_link_service.is_ack_response.return_value = True
        mock_link_service.is_nak_response.return_value = False

        mock_telegram_service = Mock()
        mock_telegram_service_class.return_value = mock_telegram_service

        # Mock ReplyTelegram
        mock_reply = Mock(spec=ReplyTelegram)
        mock_telegram_service.parse_telegram.return_value = mock_reply

        # Mock ConbusService response
        mock_response = Mock()
        mock_response.success = True
        mock_response.received_telegrams = ["<R0123450001F04D0400FH>"]
        mock_response.error = None
        mock_response.timestamp = datetime(2025, 9, 26, 13, 11, 25, 820383)
        mock_conbus_service.send_raw_telegram.return_value = mock_response

        # Test
        result = ConbusLinknumberService().set_linknumber("0123450001", 25)

        # Assertions
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is True
        assert result.result == "ACK"
        assert result.serial_number == "0123450001"
        assert result.sent_telegram == "<S0123450001F04D0425FO>"
        assert result.received_telegrams == ["<R0123450001F04D0400FH>"]
        assert result.error is None

    @patch("xp.services.conbus_linknumber_service.ConbusService")
    @patch("xp.services.conbus_linknumber_service.LinkNumberService")
    @patch("xp.services.conbus_linknumber_service.TelegramService")
    def test_set_linknumber_success_nak(
        self,
        mock_telegram_service_class,
        mock_link_service_class,
        mock_conbus_service_class,
    ):
        """Test link number setting with NAK response"""
        # Setup mocks
        mock_conbus_service = Mock()
        mock_conbus_service.__enter__ = Mock(return_value=mock_conbus_service)
        mock_conbus_service.__exit__ = Mock(return_value=None)
        mock_conbus_service_class.return_value = mock_conbus_service

        mock_link_service = Mock()
        mock_link_service_class.return_value = mock_link_service
        mock_link_service.generate_set_link_number_telegram.return_value = (
            "<S0123450001F04D0425FO>"
        )
        mock_link_service.is_ack_response.return_value = False
        mock_link_service.is_nak_response.return_value = True

        mock_telegram_service = Mock()
        mock_telegram_service_class.return_value = mock_telegram_service

        # Mock ReplyTelegram
        mock_reply = Mock(spec=ReplyTelegram)
        mock_telegram_service.parse_telegram.return_value = mock_reply

        # Mock ConbusService response
        mock_response = Mock()
        mock_response.success = True
        mock_response.received_telegrams = ["<R0123450001F19DFH>"]
        mock_response.error = None
        mock_response.timestamp = datetime(2025, 9, 26, 13, 11, 25, 820383)
        mock_conbus_service.send_raw_telegram.return_value = mock_response

        # Test
        result = ConbusLinknumberService().set_linknumber("0123450001", 25)

        # Assertions
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "NAK"
        assert result.serial_number == "0123450001"

    @patch("xp.services.conbus_linknumber_service.ConbusService")
    @patch("xp.services.conbus_linknumber_service.LinkNumberService")
    def test_set_linknumber_connection_failure(
        self, mock_link_service_class, mock_conbus_service_class
    ):
        """Test link number setting with connection failure"""
        # Setup mocks
        mock_conbus_service = Mock()
        mock_conbus_service.__enter__ = Mock(return_value=mock_conbus_service)
        mock_conbus_service.__exit__ = Mock(return_value=None)
        mock_conbus_service_class.return_value = mock_conbus_service

        mock_link_service = Mock()
        mock_link_service_class.return_value = mock_link_service
        mock_link_service.generate_set_link_number_telegram.return_value = (
            "<S0123450001F04D0425FO>"
        )

        # Mock ConbusService response for connection failure
        mock_response = Mock()
        mock_response.success = False
        mock_response.received_telegrams = []
        mock_response.error = "Connection timeout"
        mock_response.timestamp = datetime.now()
        mock_conbus_service.send_raw_telegram.return_value = mock_response

        # Test
        result = ConbusLinknumberService().set_linknumber("0123450001", 25)

        # Assertions
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "NAK"
        assert result.error == "Connection timeout"

    @patch("xp.services.conbus_linknumber_service.LinkNumberService")
    def test_set_linknumber_invalid_parameters(self, mock_link_service_class):
        """Test link number setting with invalid parameters"""
        # Setup mocks
        mock_link_service = Mock()
        mock_link_service_class.return_value = mock_link_service
        mock_link_service.generate_set_link_number_telegram.side_effect = (
            LinkNumberError("Invalid link number")
        )

        # Test
        result = ConbusLinknumberService().set_linknumber("invalid", 101)

        # Assertions
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "NAK"
        assert result.error == "Invalid link number"

    def test_context_manager(self, service):
        """Test service can be used as context manager"""
        with service as s:
            assert s is service

    @patch("xp.services.conbus_linknumber_service.ConbusService")
    @patch("xp.services.conbus_linknumber_service.LinkNumberService")
    def test_set_linknumber_no_received_telegrams(
        self,
        mock_link_service_class,
        mock_conbus_service_class,
    ):
        """Test link number setting with no received telegrams"""
        # Setup mocks
        mock_conbus_service = Mock()
        mock_conbus_service.__enter__ = Mock(return_value=mock_conbus_service)
        mock_conbus_service.__exit__ = Mock(return_value=None)
        mock_conbus_service_class.return_value = mock_conbus_service

        mock_link_service = Mock()
        mock_link_service_class.return_value = mock_link_service
        mock_link_service.generate_set_link_number_telegram.return_value = (
            "<S0123450001F04D0425FO>"
        )

        # Mock ConbusService response with no received telegrams
        mock_response = Mock()
        mock_response.success = True
        mock_response.received_telegrams = []
        mock_response.error = None
        mock_response.timestamp = datetime.now()
        mock_conbus_service.send_raw_telegram.return_value = mock_response

        # Test
        result = ConbusLinknumberService().set_linknumber("0123450001", 25)

        # Assertions
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False  # Should be False because no ACK received
        assert result.result == "NAK"

    @patch("xp.services.conbus_linknumber_service.ConbusDatapointService")
    def test_get_linknumber_success(self, mock_datapoint_service_class):
        """Test successful link number retrieval"""
        # Setup mock datapoint service
        mock_datapoint_service = Mock()
        mock_datapoint_service_class.return_value = mock_datapoint_service

        # Mock successful datapoint response
        mock_datapoint_response = Mock()
        mock_datapoint_response.success = True
        mock_datapoint_response.datapoint_telegram = Mock()
        mock_datapoint_response.datapoint_telegram.data_value = "25"
        mock_datapoint_response.sent_telegram = "<S0123450001F03D04FG>"
        mock_datapoint_response.received_telegrams = ["<R0123450001F03D041AFH>"]
        mock_datapoint_response.timestamp = datetime.now()
        mock_datapoint_service.query_datapoint.return_value = mock_datapoint_response

        # Test
        result = ConbusLinknumberService().get_linknumber("0123450001")

        # Assertions
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is True
        assert result.result == "SUCCESS"
        assert result.serial_number == "0123450001"
        assert result.link_number == 25
        assert result.sent_telegram == "<S0123450001F03D04FG>"

        # Verify datapoint service was called correctly
        from xp.models.datapoint_type import DataPointType

        mock_datapoint_service.query_datapoint.assert_called_once_with(
            DataPointType.LINK_NUMBER, "0123450001"
        )

    @patch("xp.services.conbus_linknumber_service.ConbusDatapointService")
    def test_get_linknumber_query_failed(self, mock_datapoint_service_class):
        """Test link number retrieval when datapoint query fails"""
        # Setup mock datapoint service
        mock_datapoint_service = Mock()
        mock_datapoint_service_class.return_value = mock_datapoint_service

        # Mock failed datapoint response
        mock_datapoint_response = Mock()
        mock_datapoint_response.success = False
        mock_datapoint_response.datapoint_telegram = None
        mock_datapoint_response.sent_telegram = "<S0123450001F03D04FG>"
        mock_datapoint_response.received_telegrams = []
        mock_datapoint_response.error = "Connection timeout"
        mock_datapoint_response.timestamp = datetime.now()
        mock_datapoint_service.query_datapoint.return_value = mock_datapoint_response

        # Test
        result = ConbusLinknumberService().get_linknumber("0123450001")

        # Assertions
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "QUERY_FAILED"
        assert result.serial_number == "0123450001"
        assert result.link_number is None
        assert result.error == "Connection timeout"

    @patch("xp.services.conbus_linknumber_service.ConbusDatapointService")
    def test_get_linknumber_parse_error(self, mock_datapoint_service_class):
        """Test link number retrieval when parsing fails"""
        # Setup mock datapoint service
        mock_datapoint_service = Mock()
        mock_datapoint_service_class.return_value = mock_datapoint_service

        # Mock successful datapoint response with invalid data
        mock_datapoint_response = Mock()
        mock_datapoint_response.success = True
        mock_datapoint_response.datapoint_telegram = Mock()
        mock_datapoint_response.datapoint_telegram.data_value = "invalid"
        mock_datapoint_response.sent_telegram = "<S0123450001F03D04FG>"
        mock_datapoint_response.received_telegrams = ["<R0123450001F03D04invalidFH>"]
        mock_datapoint_response.timestamp = datetime.now()
        mock_datapoint_service.query_datapoint.return_value = mock_datapoint_response

        # Test
        result = ConbusLinknumberService().get_linknumber("0123450001")

        # Assertions
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "PARSE_ERROR"
        assert result.serial_number == "0123450001"
        assert result.link_number is None
        assert (
            result.error is not None and "Failed to parse link number" in result.error
        )

    @patch("xp.services.conbus_linknumber_service.ConbusDatapointService")
    def test_get_linknumber_exception(self, mock_datapoint_service_class):
        """Test link number retrieval when exception occurs"""
        # Setup mock datapoint service that raises exception
        mock_datapoint_service = Mock()
        mock_datapoint_service_class.return_value = mock_datapoint_service
        mock_datapoint_service.query_datapoint.side_effect = Exception("Service error")

        # Test
        result = ConbusLinknumberService().get_linknumber("0123450001")

        # Assertions
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "ERROR"
        assert result.serial_number == "0123450001"
        assert result.link_number is None
        assert (
            result.error is not None
            and "Unexpected error: Service error" in result.error
        )

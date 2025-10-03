from datetime import datetime
from unittest.mock import Mock

import pytest

from xp.models.conbus.conbus_linknumber import ConbusLinknumberResponse
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.services.conbus.conbus_linknumber_service import ConbusLinknumberService
from xp.services.telegram.telegram_link_number_service import LinkNumberError


class TestConbusLinknumberService:
    """Test cases for ConbusLinknumberService"""

    @pytest.fixture
    def mock_conbus_service(self):
        """Create mock ConbusService"""
        return Mock()

    @pytest.fixture
    def mock_datapoint_service(self):
        """Create mock ConbusDatapointService"""
        return Mock()

    @pytest.fixture
    def mock_link_number_service(self):
        """Create mock LinkNumberService"""
        return Mock()

    @pytest.fixture
    def mock_telegram_service(self):
        """Create mock TelegramService"""
        return Mock()

    @pytest.fixture
    def service(
        self,
        mock_conbus_service,
        mock_datapoint_service,
        mock_link_number_service,
        mock_telegram_service,
    ):
        """Create service instance with mocked dependencies"""
        return ConbusLinknumberService(
            conbus_service=mock_conbus_service,
            datapoint_service=mock_datapoint_service,
            link_number_service=mock_link_number_service,
            telegram_service=mock_telegram_service,
        )

    def test_service_initialization(
        self,
        mock_conbus_service,
        mock_datapoint_service,
        mock_link_number_service,
        mock_telegram_service,
    ):
        """Test service initialization"""
        service = ConbusLinknumberService(
            conbus_service=mock_conbus_service,
            datapoint_service=mock_datapoint_service,
            link_number_service=mock_link_number_service,
            telegram_service=mock_telegram_service,
        )

        assert service.conbus_service is not None
        assert service.datapoint_service is not None
        assert service.link_number_service is not None
        assert service.telegram_service is not None

    def test_set_linknumber_success_ack(self):
        """Test successful link number setting with ACK response"""
        # Setup mocks
        mock_conbus_service = Mock()
        mock_conbus_service.__enter__ = Mock(return_value=mock_conbus_service)
        mock_conbus_service.__exit__ = Mock(return_value=None)

        mock_datapoint_service = Mock()

        mock_link_service = Mock()
        mock_link_service.generate_set_link_number_telegram.return_value = (
            "<S0123450001F04D0425FO>"
        )
        mock_link_service.is_ack_response.return_value = True
        mock_link_service.is_nak_response.return_value = False

        mock_telegram_service = Mock()

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

        # Create service with mocked dependencies
        # Test
        result = ConbusLinknumberService(
            conbus_service=mock_conbus_service,
            datapoint_service=mock_datapoint_service,
            link_number_service=mock_link_service,
            telegram_service=mock_telegram_service,
        ).set_linknumber("0123450001", 25)

        # Assertions
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is True
        assert result.result == "ACK"
        assert result.serial_number == "0123450001"
        assert result.sent_telegram == "<S0123450001F04D0425FO>"
        assert result.received_telegrams == ["<R0123450001F04D0400FH>"]
        assert result.error is None

    def test_set_linknumber_success_nak(self):
        """Test link number setting with NAK response"""
        # Setup mocks
        mock_conbus_service = Mock()
        mock_conbus_service.__enter__ = Mock(return_value=mock_conbus_service)
        mock_conbus_service.__exit__ = Mock(return_value=None)

        mock_datapoint_service = Mock()

        mock_link_service = Mock()
        mock_link_service.generate_set_link_number_telegram.return_value = (
            "<S0123450001F04D0425FO>"
        )
        mock_link_service.is_ack_response.return_value = False
        mock_link_service.is_nak_response.return_value = True

        mock_telegram_service = Mock()

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

        # Create service with mocked dependencies
        # Test
        result = ConbusLinknumberService(
            conbus_service=mock_conbus_service,
            datapoint_service=mock_datapoint_service,
            link_number_service=mock_link_service,
            telegram_service=mock_telegram_service,
        ).set_linknumber("0123450001", 25)

        # Assertions
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "NAK"
        assert result.serial_number == "0123450001"

    def test_set_linknumber_connection_failure(self):
        """Test link number setting with connection failure"""
        # Setup mocks
        mock_conbus_service = Mock()
        mock_conbus_service.__enter__ = Mock(return_value=mock_conbus_service)
        mock_conbus_service.__exit__ = Mock(return_value=None)

        mock_datapoint_service = Mock()

        mock_link_service = Mock()
        mock_link_service.generate_set_link_number_telegram.return_value = (
            "<S0123450001F04D0425FO>"
        )

        mock_telegram_service = Mock()

        # Mock ConbusService response for connection failure
        mock_response = Mock()
        mock_response.success = False
        mock_response.received_telegrams = []
        mock_response.error = "Connection timeout"
        mock_response.timestamp = datetime.now()
        mock_conbus_service.send_raw_telegram.return_value = mock_response

        # Create service with mocked dependencies
        # Test
        result = ConbusLinknumberService(
            conbus_service=mock_conbus_service,
            datapoint_service=mock_datapoint_service,
            link_number_service=mock_link_service,
            telegram_service=mock_telegram_service,
        ).set_linknumber("0123450001", 25)

        # Assertions
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "NAK"
        assert result.error == "Connection timeout"

    def test_set_linknumber_invalid_parameters(self):
        """Test link number setting with invalid parameters"""
        # Setup mocks
        mock_conbus_service = Mock()

        mock_datapoint_service = Mock()

        mock_link_service = Mock()
        mock_link_service.generate_set_link_number_telegram.side_effect = (
            LinkNumberError("Invalid link number")
        )

        mock_telegram_service = Mock()

        # Create service with mocked dependencies
        # Test
        result = ConbusLinknumberService(
            conbus_service=mock_conbus_service,
            datapoint_service=mock_datapoint_service,
            link_number_service=mock_link_service,
            telegram_service=mock_telegram_service,
        ).set_linknumber("invalid", 101)

        # Assertions
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "NAK"
        assert result.error == "Invalid link number"

    def test_context_manager(self, service):
        """Test service can be used as context manager"""
        with service as s:
            assert s is service

    def test_set_linknumber_no_received_telegrams(self):
        """Test link number setting with no received telegrams"""
        # Setup mocks
        mock_conbus_service = Mock()
        mock_conbus_service.__enter__ = Mock(return_value=mock_conbus_service)
        mock_conbus_service.__exit__ = Mock(return_value=None)

        mock_datapoint_service = Mock()

        mock_link_service = Mock()
        mock_link_service.generate_set_link_number_telegram.return_value = (
            "<S0123450001F04D0425FO>"
        )

        mock_telegram_service = Mock()

        # Mock ConbusService response with no received telegrams
        mock_response = Mock()
        mock_response.success = True
        mock_response.received_telegrams = []
        mock_response.error = None
        mock_response.timestamp = datetime.now()
        mock_conbus_service.send_raw_telegram.return_value = mock_response

        # Create service with mocked dependencies
        # Test
        result = ConbusLinknumberService(
            conbus_service=mock_conbus_service,
            datapoint_service=mock_datapoint_service,
            link_number_service=mock_link_service,
            telegram_service=mock_telegram_service,
        ).set_linknumber("0123450001", 25)

        # Assertions
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False  # Should be False because no ACK received
        assert result.result == "NAK"

    def test_get_linknumber_success(self):
        """Test successful link number retrieval"""
        # Setup mocks
        mock_conbus_service = Mock()

        mock_datapoint_service = Mock()

        # Mock successful datapoint response
        mock_datapoint_response = Mock()
        mock_datapoint_response.success = True
        mock_datapoint_response.datapoint_telegram = Mock()
        mock_datapoint_response.datapoint_telegram.data_value = "25"
        mock_datapoint_response.sent_telegram = "<S0123450001F03D04FG>"
        mock_datapoint_response.received_telegrams = ["<R0123450001F03D041AFH>"]
        mock_datapoint_response.timestamp = datetime.now()
        mock_datapoint_service.query_datapoint.return_value = mock_datapoint_response

        mock_link_service = Mock()

        mock_telegram_service = Mock()

        # Create service with mocked dependencies
        # Test
        result = ConbusLinknumberService(
            conbus_service=mock_conbus_service,
            datapoint_service=mock_datapoint_service,
            link_number_service=mock_link_service,
            telegram_service=mock_telegram_service,
        ).get_linknumber("0123450001")

        # Assertions
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is True
        assert result.result == "SUCCESS"
        assert result.serial_number == "0123450001"
        assert result.link_number == 25
        assert result.sent_telegram == "<S0123450001F03D04FG>"

        # Verify datapoint service was called correctly
        from xp.models.telegram.datapoint_type import DataPointType

        mock_datapoint_service.query_datapoint.assert_called_once_with(
            DataPointType.LINK_NUMBER, "0123450001"
        )

    def test_get_linknumber_query_failed(self):
        """Test link number retrieval when datapoint query fails"""
        # Setup mocks
        mock_conbus_service = Mock()

        mock_datapoint_service = Mock()

        # Mock failed datapoint response
        mock_datapoint_response = Mock()
        mock_datapoint_response.success = False
        mock_datapoint_response.datapoint_telegram = None
        mock_datapoint_response.sent_telegram = "<S0123450001F03D04FG>"
        mock_datapoint_response.received_telegrams = []
        mock_datapoint_response.error = "Connection timeout"
        mock_datapoint_response.timestamp = datetime.now()
        mock_datapoint_service.query_datapoint.return_value = mock_datapoint_response

        mock_link_service = Mock()

        mock_telegram_service = Mock()

        # Create service with mocked dependencies
        # Test
        result = ConbusLinknumberService(
            conbus_service=mock_conbus_service,
            datapoint_service=mock_datapoint_service,
            link_number_service=mock_link_service,
            telegram_service=mock_telegram_service,
        ).get_linknumber("0123450001")

        # Assertions
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "QUERY_FAILED"
        assert result.serial_number == "0123450001"
        assert result.link_number is None
        assert result.error == "Connection timeout"

    def test_get_linknumber_parse_error(self):
        """Test link number retrieval when parsing fails"""
        # Setup mocks
        mock_conbus_service = Mock()

        mock_datapoint_service = Mock()

        # Mock successful datapoint response with invalid data
        mock_datapoint_response = Mock()
        mock_datapoint_response.success = True
        mock_datapoint_response.datapoint_telegram = Mock()
        mock_datapoint_response.datapoint_telegram.data_value = "invalid"
        mock_datapoint_response.sent_telegram = "<S0123450001F03D04FG>"
        mock_datapoint_response.received_telegrams = ["<R0123450001F03D04invalidFH>"]
        mock_datapoint_response.timestamp = datetime.now()
        mock_datapoint_service.query_datapoint.return_value = mock_datapoint_response

        mock_link_service = Mock()

        mock_telegram_service = Mock()

        # Create service with mocked dependencies
        # Test
        result = ConbusLinknumberService(
            conbus_service=mock_conbus_service,
            datapoint_service=mock_datapoint_service,
            link_number_service=mock_link_service,
            telegram_service=mock_telegram_service,
        ).get_linknumber("0123450001")

        # Assertions
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "PARSE_ERROR"
        assert result.serial_number == "0123450001"
        assert result.link_number is None
        assert (
            result.error is not None and "Failed to parse link number" in result.error
        )

    def test_get_linknumber_exception(self):
        """Test link number retrieval when exception occurs"""
        # Setup mocks
        mock_conbus_service = Mock()

        # Setup mock datapoint service that raises exception
        mock_datapoint_service = Mock()
        mock_datapoint_service.query_datapoint.side_effect = Exception("Service error")

        mock_link_service = Mock()

        mock_telegram_service = Mock()

        # Create service with mocked dependencies
        # Test
        result = ConbusLinknumberService(
            conbus_service=mock_conbus_service,
            datapoint_service=mock_datapoint_service,
            link_number_service=mock_link_service,
            telegram_service=mock_telegram_service,
        ).get_linknumber("0123450001")

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

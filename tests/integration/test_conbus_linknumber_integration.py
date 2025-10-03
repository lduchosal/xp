"""Integration tests for Conbus link number functionality"""

from unittest.mock import Mock

from xp.models.conbus.conbus_linknumber import ConbusLinknumberResponse
from xp.services.conbus.conbus_linknumber_service import ConbusLinknumberService


class TestConbusLinknumberIntegration:
    """Integration test cases for Conbus link number operations"""

    @staticmethod
    def _create_mock_conbus_response(
        success=True, serial_number="0123450001", error=None, telegrams=None
    ):
        """Helper to create a properly formed ConbusResponse"""
        if telegrams is None:
            telegrams = [f"<R{serial_number}F18DFA>"] if success else []

        mock_response = Mock()
        mock_response.success = success
        mock_response.sent_telegram = f"<S{serial_number}F04D0425FO>"
        mock_response.received_telegrams = telegrams
        mock_response.error = error
        mock_response.timestamp = Mock()
        return mock_response

    def _create_mock_conbus_service(self, success=True, ack_response=True):
        """Helper to create a properly mocked ConbusService"""
        mock_conbus_instance = Mock()
        mock_conbus_instance.__enter__ = Mock(return_value=mock_conbus_instance)
        mock_conbus_instance.__exit__ = Mock(return_value=False)

        # Configure response based on test scenario
        if success and ack_response:
            telegrams = ["<R0123450001F18DFA>"]  # ACK response
        elif success and not ack_response:
            telegrams = ["<R0123450001F19DFB>"]  # NAK response
        else:
            telegrams = []

        response = self._create_mock_conbus_response(
            success=success, telegrams=telegrams
        )
        mock_conbus_instance.send_raw_telegram.return_value = response
        return mock_conbus_instance

    def test_conbus_linknumber_valid(self):
        """Test setting valid link number"""
        # Mock service dependencies
        mock_telegram_service = Mock()
        mock_conbus_service = Mock()
        mock_datapoint_service = Mock()
        mock_link_number_service = Mock()

        # Setup mock conbus service with context manager
        # The service code does: with self.conbus_service: ... self.conbus_service.send_raw_telegram()
        # So we need __enter__ and __exit__ on the service itself, AND the method on it
        mock_conbus_service.__enter__ = Mock(return_value=mock_conbus_service)
        mock_conbus_service.__exit__ = Mock(return_value=False)

        # Create proper response with list
        mock_response = Mock()
        mock_response.success = True
        mock_response.received_telegrams = ["<R0123450001F18DFA>"]  # ACK response
        mock_response.error = None
        mock_response.timestamp = Mock()
        mock_conbus_service.send_raw_telegram.return_value = mock_response

        # Setup telegram parsing - parse_telegram should return a ReplyTelegram
        from xp.models.telegram.reply_telegram import ReplyTelegram

        mock_reply = ReplyTelegram(checksum="DFA", raw_telegram="<R0123450001F18DFA>")
        mock_telegram_service.parse_telegram.return_value = mock_reply
        mock_link_number_service.is_ack_response.return_value = True
        mock_link_number_service.is_nak_response.return_value = False
        mock_link_number_service.generate_set_link_number_telegram.return_value = (
            "<S0123450001F04D0425FG>"
        )

        # Test
        result = ConbusLinknumberService(
            conbus_service=mock_conbus_service,
            datapoint_service=mock_datapoint_service,
            link_number_service=mock_link_number_service,
            telegram_service=mock_telegram_service,
        ).set_linknumber("0123450001", 25)

        # Verify
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is True
        assert result.result == "ACK"
        assert result.serial_number == "0123450001"
        assert result.error is None

        # Verify service was called correctly
        mock_conbus_service.send_raw_telegram.assert_called_once()
        args = mock_conbus_service.send_raw_telegram.call_args[0]
        assert args[0] == "<S0123450001F04D0425FG>"

    def test_conbus_linknumber_invalid_response(self):
        """Test handling invalid/NAK responses"""
        # Mock service dependencies
        mock_telegram_service = Mock()
        mock_conbus_service = Mock()
        mock_datapoint_service = Mock()
        mock_link_number_service = Mock()

        # Setup mock for NAK response
        mock_conbus_instance = self._create_mock_conbus_service(
            success=True, ack_response=False
        )
        mock_conbus_service.__enter__ = Mock(return_value=mock_conbus_instance)
        mock_conbus_service.__exit__ = Mock(return_value=False)

        # Setup telegram parsing for NAK
        mock_reply = Mock()
        mock_telegram_service.parse_telegram.return_value = mock_reply
        mock_link_number_service.is_ack_response.return_value = False
        mock_link_number_service.is_nak_response.return_value = True
        mock_link_number_service.generate_set_link_number_telegram.return_value = (
            "<S0123450001F04D0425FG>"
        )

        # Test
        result = ConbusLinknumberService(
            conbus_service=mock_conbus_service,
            datapoint_service=mock_datapoint_service,
            link_number_service=mock_link_number_service,
            telegram_service=mock_telegram_service,
        ).set_linknumber("0123450001", 25)

        # Verify
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "NAK"
        assert result.serial_number == "0123450001"

    def test_conbus_linknumber_connection_failure(self):
        """Test handling connection failures"""
        # Mock service dependencies
        mock_telegram_service = Mock()
        mock_conbus_service = Mock()
        mock_datapoint_service = Mock()
        mock_link_number_service = Mock()

        # Setup mock for connection failure
        mock_conbus_instance = self._create_mock_conbus_service(success=False)
        mock_conbus_service.__enter__ = Mock(return_value=mock_conbus_instance)
        mock_conbus_service.__exit__ = Mock(return_value=False)

        # Setup telegram generation
        mock_link_number_service.generate_set_link_number_telegram.return_value = (
            "<S0123450001F04D0425FG>"
        )

        # Test
        result = ConbusLinknumberService(
            conbus_service=mock_conbus_service,
            datapoint_service=mock_datapoint_service,
            link_number_service=mock_link_number_service,
            telegram_service=mock_telegram_service,
        ).set_linknumber("0123450001", 25)

        # Verify
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "NAK"
        assert result.serial_number == "0123450001"

    def test_conbus_linknumber_invalid_serial_number(self):
        """Test handling invalid serial number"""
        # Mock service dependencies
        mock_telegram_service = Mock()
        mock_conbus_service = Mock()
        mock_datapoint_service = Mock()
        mock_link_number_service = Mock()

        # Setup link number service to raise error for invalid serial
        from xp.services.telegram.telegram_link_number_service import LinkNumberError

        mock_link_number_service.generate_set_link_number_telegram.side_effect = (
            LinkNumberError("Serial number must be 10 digits")
        )

        # Test
        result = ConbusLinknumberService(
            conbus_service=mock_conbus_service,
            datapoint_service=mock_datapoint_service,
            link_number_service=mock_link_number_service,
            telegram_service=mock_telegram_service,
        ).set_linknumber("invalid", 25)

        # Verify
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "NAK"
        assert result.serial_number == "invalid"
        assert (
            result.error is not None
            and "Serial number must be 10 digits" in result.error
        )

    def test_conbus_linknumber_invalid_link_number(self):
        """Test handling invalid link number"""
        # Mock service dependencies
        mock_telegram_service = Mock()
        mock_conbus_service = Mock()
        mock_datapoint_service = Mock()
        mock_link_number_service = Mock()

        # Setup link number service to raise error for invalid link number
        from xp.services.telegram.telegram_link_number_service import LinkNumberError

        mock_link_number_service.generate_set_link_number_telegram.side_effect = (
            LinkNumberError("Link number must be between 0-99")
        )

        # Test
        result = ConbusLinknumberService(
            conbus_service=mock_conbus_service,
            datapoint_service=mock_datapoint_service,
            link_number_service=mock_link_number_service,
            telegram_service=mock_telegram_service,
        ).set_linknumber("0123450001", 101)

        # Verify
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "NAK"
        assert result.serial_number == "0123450001"
        assert (
            result.error is not None
            and "Link number must be between 0-99" in result.error
        )

    def test_conbus_linknumber_edge_cases(self):
        """Test edge cases for link number values"""
        # Mock service dependencies
        mock_telegram_service = Mock()
        mock_conbus_service = Mock()
        mock_datapoint_service = Mock()
        mock_link_number_service = Mock()

        # Setup mock conbus service with context manager
        # The service code does: with self.conbus_service: ... self.conbus_service.send_raw_telegram()
        # So we need __enter__ and __exit__ on the service itself, AND the method on it
        mock_conbus_service.__enter__ = Mock(return_value=mock_conbus_service)
        mock_conbus_service.__exit__ = Mock(return_value=False)

        # Create proper response with list
        mock_response = Mock()
        mock_response.success = True
        mock_response.received_telegrams = ["<R0123450001F18DFA>"]  # ACK response
        mock_response.error = None
        mock_response.timestamp = Mock()
        mock_conbus_service.send_raw_telegram.return_value = mock_response

        # Setup telegram parsing - parse_telegram should return a ReplyTelegram
        from xp.models.telegram.reply_telegram import ReplyTelegram

        mock_reply = ReplyTelegram(checksum="DFA", raw_telegram="<R0123450001F18DFA>")
        mock_telegram_service.parse_telegram.return_value = mock_reply
        mock_link_number_service.is_ack_response.return_value = True
        mock_link_number_service.is_nak_response.return_value = False
        mock_link_number_service.generate_set_link_number_telegram.return_value = (
            "<S0123450001F04D0425FG>"
        )

        service = ConbusLinknumberService(
            conbus_service=mock_conbus_service,
            datapoint_service=mock_datapoint_service,
            link_number_service=mock_link_number_service,
            telegram_service=mock_telegram_service,
        )

        # Test minimum value
        result = service.set_linknumber("0123450001", 0)
        assert result.success is True
        assert result.result == "ACK"

        # Test maximum value
        result = service.set_linknumber("0123450001", 99)
        assert result.success is True
        assert result.result == "ACK"

    def test_service_context_manager(self):
        """Test service can be used as context manager"""
        # Mock service dependencies
        mock_telegram_service = Mock()
        mock_conbus_service = Mock()
        mock_datapoint_service = Mock()
        mock_link_number_service = Mock()

        service = ConbusLinknumberService(
            conbus_service=mock_conbus_service,
            datapoint_service=mock_datapoint_service,
            link_number_service=mock_link_number_service,
            telegram_service=mock_telegram_service,
        )

        with service as s:
            assert s is service

    @staticmethod
    def _create_mock_datapoint_response(
        success=True, serial_number="0123450001", link_number=25, error=None
    ):
        """Helper to create a properly formed ConbusDatapointResponse"""
        mock_response = Mock()
        mock_response.success = success
        mock_response.sent_telegram = f"<S{serial_number}F03D04FG>"
        mock_response.received_telegrams = (
            [f"<R{serial_number}F03D04{link_number:02d}FH>"] if success else []
        )
        mock_response.error = error
        mock_response.timestamp = Mock()

        if success:
            mock_response.datapoint_telegram = Mock()
            mock_response.datapoint_telegram.data_value = str(link_number)
        else:
            mock_response.datapoint_telegram = None

        return mock_response

    def test_conbus_get_linknumber_valid(self):
        """Test getting valid link number"""
        # Mock service dependencies
        mock_telegram_service = Mock()
        mock_conbus_service = Mock()
        mock_datapoint_service = Mock()
        mock_link_number_service = Mock()

        # Setup mock datapoint response
        datapoint_response = self._create_mock_datapoint_response(
            success=True, serial_number="0123450001", link_number=25
        )
        mock_datapoint_service.query_datapoint.return_value = datapoint_response

        # Test
        result = ConbusLinknumberService(
            conbus_service=mock_conbus_service,
            datapoint_service=mock_datapoint_service,
            link_number_service=mock_link_number_service,
            telegram_service=mock_telegram_service,
        ).get_linknumber("0123450001")

        # Verify
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is True
        assert result.result == "SUCCESS"
        assert result.serial_number == "0123450001"
        assert result.link_number == 25
        assert result.error is None

        # Verify service was called correctly
        from xp.models.telegram.datapoint_type import DataPointType

        mock_datapoint_service.query_datapoint.assert_called_once_with(
            DataPointType.LINK_NUMBER, "0123450001"
        )

    def test_conbus_get_linknumber_query_failed(self):
        """Test handling datapoint query failures"""
        # Mock service dependencies
        mock_telegram_service = Mock()
        mock_conbus_service = Mock()
        mock_datapoint_service = Mock()
        mock_link_number_service = Mock()

        # Setup mock for query failure
        datapoint_response = self._create_mock_datapoint_response(
            success=False, error="Connection timeout"
        )
        mock_datapoint_service.query_datapoint.return_value = datapoint_response

        # Test
        result = ConbusLinknumberService(
            conbus_service=mock_conbus_service,
            datapoint_service=mock_datapoint_service,
            link_number_service=mock_link_number_service,
            telegram_service=mock_telegram_service,
        ).get_linknumber("0123450001")

        # Verify
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "QUERY_FAILED"
        assert result.serial_number == "0123450001"
        assert result.link_number is None
        assert result.error is not None and "Connection timeout" in result.error

    def test_conbus_get_linknumber_parse_error(self):
        """Test handling invalid link number data"""
        # Mock service dependencies
        mock_telegram_service = Mock()
        mock_conbus_service = Mock()
        mock_datapoint_service = Mock()
        mock_link_number_service = Mock()

        # Setup mock with invalid data
        mock_response = Mock()
        mock_response.success = True
        mock_response.sent_telegram = "<S0123450001F03D04FG>"
        mock_response.received_telegrams = ["<R0123450001F03D04invalidFH>"]
        mock_response.error = None
        mock_response.timestamp = Mock()
        mock_response.datapoint_telegram = Mock()
        mock_response.datapoint_telegram.data_value = "invalid"

        mock_datapoint_service.query_datapoint.return_value = mock_response

        # Test
        result = ConbusLinknumberService(
            conbus_service=mock_conbus_service,
            datapoint_service=mock_datapoint_service,
            link_number_service=mock_link_number_service,
            telegram_service=mock_telegram_service,
        ).get_linknumber("0123450001")

        # Verify
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "PARSE_ERROR"
        assert result.serial_number == "0123450001"
        assert result.link_number is None
        assert (
            result.error is not None and "Failed to parse link number" in result.error
        )

    def test_conbus_get_linknumber_service_exception(self):
        """Test handling service exceptions"""
        # Mock service dependencies
        mock_telegram_service = Mock()
        mock_conbus_service = Mock()
        mock_datapoint_service = Mock()
        mock_link_number_service = Mock()

        # Setup mock that raises exception
        mock_datapoint_service.query_datapoint.side_effect = Exception(
            "Service unavailable"
        )

        # Test
        result = ConbusLinknumberService(
            conbus_service=mock_conbus_service,
            datapoint_service=mock_datapoint_service,
            link_number_service=mock_link_number_service,
            telegram_service=mock_telegram_service,
        ).get_linknumber("0123450001")

        # Verify
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "ERROR"
        assert result.serial_number == "0123450001"
        assert result.link_number is None
        assert (
            result.error is not None
            and "Unexpected error: Service unavailable" in result.error
        )

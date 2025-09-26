"""Integration tests for Conbus link number functionality"""

from unittest.mock import Mock, patch

from xp.services.conbus_linknumber_service import ConbusLinknumberService
from xp.models.conbus_linknumber import ConbusLinknumberResponse


class TestConbusLinknumberIntegration:
    """Integration test cases for Conbus link number operations"""

    @staticmethod
    def _create_mock_conbus_response(success=True, serial_number="0020045057", error=None, telegrams=None):
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
            telegrams = ["<R0020045057F18DFA>"]  # ACK response
        elif success and not ack_response:
            telegrams = ["<R0020045057F19DFB>"]  # NAK response
        else:
            telegrams = []

        response = self._create_mock_conbus_response(
            success=success,
            telegrams=telegrams
        )
        mock_conbus_instance.send_raw_telegram.return_value = response
        return mock_conbus_instance

    @patch('xp.services.conbus_linknumber_service.ConbusService')
    def test_conbus_linknumber_valid(self, mock_conbus_service_class):
        """Test setting valid link number"""
        # Setup mock
        mock_service = self._create_mock_conbus_service(success=True, ack_response=True)
        mock_conbus_service_class.return_value = mock_service

        # Test
        service = ConbusLinknumberService("test.yml")
        result = service.set_linknumber("0020045057", 25)

        # Verify
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is True
        assert result.result == "ACK"
        assert result.serial_number == "0020045057"
        assert result.error is None

        # Verify service was called correctly
        mock_service.send_raw_telegram.assert_called_once()
        args = mock_service.send_raw_telegram.call_args[0]
        assert args[0] == "<S0020045057F04D0425FH>"

    @patch('xp.services.conbus_linknumber_service.ConbusService')
    def test_conbus_linknumber_invalid_response(self, mock_conbus_service_class):
        """Test handling invalid/NAK responses"""
        # Setup mock for NAK response
        mock_service = self._create_mock_conbus_service(success=True, ack_response=False)
        mock_conbus_service_class.return_value = mock_service

        # Test
        service = ConbusLinknumberService("test.yml")
        result = service.set_linknumber("0020045057", 25)

        # Verify
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "NAK"
        assert result.serial_number == "0020045057"

    @patch('xp.services.conbus_linknumber_service.ConbusService')
    def test_conbus_linknumber_connection_failure(self, mock_conbus_service_class):
        """Test handling connection failures"""
        # Setup mock for connection failure
        mock_service = self._create_mock_conbus_service(success=False)
        mock_conbus_service_class.return_value = mock_service

        # Test
        service = ConbusLinknumberService("test.yml")
        result = service.set_linknumber("0020045057", 25)

        # Verify
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "NAK"
        assert result.serial_number == "0020045057"

    def test_conbus_linknumber_invalid_serial_number(self):
        """Test handling invalid serial number"""
        service = ConbusLinknumberService("test.yml")
        result = service.set_linknumber("invalid", 25)

        # Verify
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "NAK"
        assert result.serial_number == "invalid"
        assert result.error is not None and "Serial number must be 10 digits" in result.error

    def test_conbus_linknumber_invalid_link_number(self):
        """Test handling invalid link number"""
        service = ConbusLinknumberService("test.yml")
        result = service.set_linknumber("0020045057", 101)

        # Verify
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "NAK"
        assert result.serial_number == "0020045057"
        assert result.error is not None and "Link number must be between 0-99" in result.error

    @patch('xp.services.conbus_linknumber_service.ConbusService')
    def test_conbus_linknumber_edge_cases(self, mock_conbus_service_class):
        """Test edge cases for link number values"""
        # Setup mock
        mock_service = self._create_mock_conbus_service(success=True, ack_response=True)
        mock_conbus_service_class.return_value = mock_service

        service = ConbusLinknumberService("test.yml")

        # Test minimum value
        result = service.set_linknumber("0020045057", 0)
        assert result.success is True
        assert result.result == "ACK"

        # Test maximum value
        result = service.set_linknumber("0020045057", 99)
        assert result.success is True
        assert result.result == "ACK"

    def test_service_context_manager(self):
        """Test service can be used as context manager"""
        service = ConbusLinknumberService("test.yml")

        with service as s:
            assert s is service
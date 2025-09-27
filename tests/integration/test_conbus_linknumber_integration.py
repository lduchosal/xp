"""Integration tests for Conbus link number functionality"""

from unittest.mock import Mock, patch

from xp.services.conbus_linknumber_service import ConbusLinknumberService
from xp.models.conbus_linknumber import ConbusLinknumberResponse


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

    @patch("xp.services.conbus_linknumber_service.ConbusService")
    def test_conbus_linknumber_valid(self, mock_conbus_service_class):
        """Test setting valid link number"""
        # Setup mock
        mock_service = self._create_mock_conbus_service(success=True, ack_response=True)
        mock_conbus_service_class.return_value = mock_service

        # Test
        result = ConbusLinknumberService("test.yml").set_linknumber("0123450001", 25)

        # Verify
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is True
        assert result.result == "ACK"
        assert result.serial_number == "0123450001"
        assert result.error is None

        # Verify service was called correctly
        mock_service.send_raw_telegram.assert_called_once()
        args = mock_service.send_raw_telegram.call_args[0]
        assert args[0] == "<S0123450001F04D0425FG>"

    @patch("xp.services.conbus_linknumber_service.ConbusService")
    def test_conbus_linknumber_invalid_response(self, mock_conbus_service_class):
        """Test handling invalid/NAK responses"""
        # Setup mock for NAK response
        mock_service = self._create_mock_conbus_service(
            success=True, ack_response=False
        )
        mock_conbus_service_class.return_value = mock_service

        # Test
        result = ConbusLinknumberService("test.yml").set_linknumber("0123450001", 25)

        # Verify
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "NAK"
        assert result.serial_number == "0123450001"

    @patch("xp.services.conbus_linknumber_service.ConbusService")
    def test_conbus_linknumber_connection_failure(self, mock_conbus_service_class):
        """Test handling connection failures"""
        # Setup mock for connection failure
        mock_service = self._create_mock_conbus_service(success=False)
        mock_conbus_service_class.return_value = mock_service

        # Test
        result = ConbusLinknumberService("test.yml").set_linknumber("0123450001", 25)

        # Verify
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "NAK"
        assert result.serial_number == "0123450001"

    def test_conbus_linknumber_invalid_serial_number(self):
        """Test handling invalid serial number"""
        result = ConbusLinknumberService("test.yml").set_linknumber("invalid", 25)

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
        result = ConbusLinknumberService("test.yml").set_linknumber("0123450001", 101)

        # Verify
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "NAK"
        assert result.serial_number == "0123450001"
        assert (
            result.error is not None
            and "Link number must be between 0-99" in result.error
        )

    @patch("xp.services.conbus_linknumber_service.ConbusService")
    def test_conbus_linknumber_edge_cases(self, mock_conbus_service_class):
        """Test edge cases for link number values"""
        # Setup mock
        mock_service = self._create_mock_conbus_service(success=True, ack_response=True)
        mock_conbus_service_class.return_value = mock_service

        service = ConbusLinknumberService("test.yml")

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
        service = ConbusLinknumberService("test.yml")

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

    @patch("xp.services.conbus_linknumber_service.ConbusDatapointService")
    def test_conbus_get_linknumber_valid(self, mock_datapoint_service_class):
        """Test getting valid link number"""
        # Setup mock
        mock_datapoint_service = Mock()
        mock_datapoint_service_class.return_value = mock_datapoint_service

        datapoint_response = self._create_mock_datapoint_response(
            success=True, serial_number="0123450001", link_number=25
        )
        mock_datapoint_service.query_datapoint.return_value = datapoint_response

        # Test
        result = ConbusLinknumberService().get_linknumber("0123450001")

        # Verify
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is True
        assert result.result == "SUCCESS"
        assert result.serial_number == "0123450001"
        assert result.link_number == 25
        assert result.error is None

        # Verify service was called correctly
        from xp.models.datapoint_type import DataPointType

        mock_datapoint_service.query_datapoint.assert_called_once_with(
            DataPointType.LINK_NUMBER, "0123450001"
        )

    @patch("xp.services.conbus_linknumber_service.ConbusDatapointService")
    def test_conbus_get_linknumber_query_failed(self, mock_datapoint_service_class):
        """Test handling datapoint query failures"""
        # Setup mock for query failure
        mock_datapoint_service = Mock()
        mock_datapoint_service_class.return_value = mock_datapoint_service

        datapoint_response = self._create_mock_datapoint_response(
            success=False, error="Connection timeout"
        )
        mock_datapoint_service.query_datapoint.return_value = datapoint_response

        # Test
        result = ConbusLinknumberService().get_linknumber("0123450001")

        # Verify
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "QUERY_FAILED"
        assert result.serial_number == "0123450001"
        assert result.link_number is None
        assert result.error is not None and "Connection timeout" in result.error

    @patch("xp.services.conbus_linknumber_service.ConbusDatapointService")
    def test_conbus_get_linknumber_parse_error(self, mock_datapoint_service_class):
        """Test handling invalid link number data"""
        # Setup mock with invalid data
        mock_datapoint_service = Mock()
        mock_datapoint_service_class.return_value = mock_datapoint_service

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
        result = ConbusLinknumberService().get_linknumber("0123450001")

        # Verify
        assert isinstance(result, ConbusLinknumberResponse)
        assert result.success is False
        assert result.result == "PARSE_ERROR"
        assert result.serial_number == "0123450001"
        assert result.link_number is None
        assert (
            result.error is not None and "Failed to parse link number" in result.error
        )

    @patch("xp.services.conbus_linknumber_service.ConbusDatapointService")
    def test_conbus_get_linknumber_service_exception(
        self, mock_datapoint_service_class
    ):
        """Test handling service exceptions"""
        # Setup mock that raises exception
        mock_datapoint_service = Mock()
        mock_datapoint_service_class.return_value = mock_datapoint_service
        mock_datapoint_service.query_datapoint.side_effect = Exception(
            "Service unavailable"
        )

        # Test
        result = ConbusLinknumberService().get_linknumber("0123450001")

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

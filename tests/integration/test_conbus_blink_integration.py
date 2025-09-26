"""Integration tests for Conbus blink functionality"""

from unittest.mock import Mock, patch

from xp.models.conbus import ConbusRequest, ConbusResponse
from xp.models.system_function import SystemFunction
from xp.services.conbus_blink_service import ConbusBlinkService


class TestConbusBlinkIntegration:
    """Integration test cases for Conbus blink operations"""

    @staticmethod
    def _create_mock_conbus_response(
        success=True, serial_number="0012345008", error=None, telegrams=None
    ):
        """Helper to create a properly formed ConbusResponse"""
        mock_request = ConbusRequest(
            serial_number=serial_number, function_code="F05", data="D00"
        )
        if telegrams is None:
            telegrams = [f"<R{serial_number}F18DFA>"] if success else []

        return ConbusResponse(
            success=success,
            request=mock_request,
            sent_telegram=f"<S{serial_number}F05D00FN>",
            received_telegrams=telegrams,
            error=error,
        )

    def _create_mock_conbus_service(
        self, discover_devices=None, discover_success=True, blink_success=True
    ):
        """Helper to create a properly mocked ConbusService"""
        if discover_devices is None:
            discover_devices = ["0012345008", "0012345011"]

        mock_conbus_instance = Mock()
        mock_conbus_instance.__enter__ = Mock(return_value=mock_conbus_instance)
        mock_conbus_instance.__exit__ = Mock(return_value=False)

        # Mock discover response
        discover_telegrams = (
            ["\n".join([f"<R{device}F01DFI>" for device in discover_devices])]
            if discover_success
            else []
        )
        discover_response = self._create_mock_conbus_response(
            success=discover_success, telegrams=discover_telegrams
        )

        # Mock blink response
        blink_response = self._create_mock_conbus_response(success=blink_success)

        # Configure the mock
        mock_conbus_instance.send_raw_telegram.return_value = discover_response
        mock_conbus_instance.send_raw_telegrams.return_value = blink_response

        return mock_conbus_instance

    @patch("xp.services.conbus_blink_service.ConbusService")
    def test_conbus_blink_all_off(self, mock_conbus_service):
        """Test turning all device blinks off"""
        mock_conbus_instance = self._create_mock_conbus_service()
        mock_conbus_service.return_value = mock_conbus_instance

        service = ConbusBlinkService()

        with service:
            response = service.blink_all("off")

        # Verify response
        assert response.success is True
        assert response.serial_number == "all"
        assert response.operation == "off"
        assert response.system_function == SystemFunction.UNBLINK

        # Verify discover telegram was sent
        mock_conbus_instance.send_raw_telegram.assert_called_once()
        # Verify blink telegrams were sent
        mock_conbus_instance.send_raw_telegrams.assert_called_once()

    @patch("xp.services.conbus_blink_service.ConbusService")
    def test_conbus_blink_all_on(self, mock_conbus_service):
        """Test turning all device blinks on"""
        mock_conbus_instance = self._create_mock_conbus_service()
        mock_conbus_service.return_value = mock_conbus_instance

        service = ConbusBlinkService()

        with service:
            response = service.blink_all("on")

        # Verify response
        assert response.success is True
        assert response.serial_number == "all"
        assert response.operation == "on"
        assert response.system_function == SystemFunction.BLINK

        # Verify discover telegram was sent
        mock_conbus_instance.send_raw_telegram.assert_called_once()
        # Verify blink telegrams were sent
        mock_conbus_instance.send_raw_telegrams.assert_called_once()

    @patch("xp.services.conbus_blink_service.ConbusService")
    def test_conbus_blink_connection_error(self, mock_conbus_service):
        """Handle network failures"""
        mock_conbus_instance = self._create_mock_conbus_service(discover_success=False)
        mock_conbus_service.return_value = mock_conbus_instance

        service = ConbusBlinkService()

        with service:
            response = service.blink_all("off")

        # Verify error response
        assert response.success is False
        assert response.serial_number == "all"
        assert response.operation == "off"
        assert response.system_function == SystemFunction.UNBLINK
        assert response.error == "Failed to discover devices"

    @patch("xp.services.conbus_blink_service.ConbusService")
    def test_conbus_blink_invalid_response(self, mock_conbus_service):
        """Handle invalid responses"""
        mock_conbus_instance = self._create_mock_conbus_service(discover_devices=[])
        mock_conbus_service.return_value = mock_conbus_instance

        service = ConbusBlinkService()

        with service:
            response = service.blink_all("off")

        # Verify response for no devices
        assert (
            response.success is True
        )  # Success because discover worked, just no devices
        assert response.serial_number == "all"
        assert response.operation == "off"
        assert response.system_function == SystemFunction.UNBLINK
        assert response.error == "No devices discovered"

    @patch("xp.services.conbus_blink_service.ConbusService")
    def test_conbus_blink_partial_failure(self, mock_conbus_service):
        """Test scenario where some devices fail to blink"""
        mock_conbus_instance = self._create_mock_conbus_service(blink_success=False)
        mock_conbus_service.return_value = mock_conbus_instance

        service = ConbusBlinkService()

        with service:
            response = service.blink_all("on")

        # Verify partial failure response
        assert response.success is False  # Should be False because blink sending failed
        assert response.serial_number == "all"
        assert response.operation == "on"
        assert response.system_function == SystemFunction.BLINK

        # Verify discover telegram was sent
        mock_conbus_instance.send_raw_telegram.assert_called_once()
        # Verify blink telegrams were attempted to be sent
        mock_conbus_instance.send_raw_telegrams.assert_called_once()

    def test_conbus_blink_service_context_manager(self):
        """Test that the service works properly as a context manager"""
        service = ConbusBlinkService()

        # Test entering and exiting context manager
        with service:
            assert service is not None

        # Should not raise any exceptions

    @patch("xp.services.conbus_blink_service.ConbusService")
    def test_conbus_blink_all_multiple_devices(self, mock_conbus_service):
        """Test blinking multiple devices successfully"""
        devices = ["0012345008", "0012345011", "1234567890", "9876543210"]
        mock_conbus_instance = self._create_mock_conbus_service(
            discover_devices=devices
        )
        mock_conbus_service.return_value = mock_conbus_instance

        service = ConbusBlinkService()

        with service:
            response = service.blink_all("on")

        # Verify all devices were processed
        assert response.success is True
        assert response.serial_number == "all"
        assert response.operation == "on"
        assert response.system_function == SystemFunction.BLINK

        # Verify discover telegram was sent
        mock_conbus_instance.send_raw_telegram.assert_called_once()
        # Verify blink telegrams were sent (should be called once with list of telegrams)
        mock_conbus_instance.send_raw_telegrams.assert_called_once()

        # Verify the telegrams list contains the right number of telegrams
        call_args = mock_conbus_instance.send_raw_telegrams.call_args[0][0]
        assert len(call_args) == len(devices)

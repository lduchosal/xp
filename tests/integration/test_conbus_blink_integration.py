"""Integration tests for Conbus blink functionality"""

from unittest.mock import Mock, patch

from xp.models.conbus import ConbusRequest, ConbusResponse
from xp.models.conbus_blink import ConbusBlinkResponse
from xp.models.conbus_discover import ConbusDiscoverResponse
from xp.models.system_function import SystemFunction
from xp.services.conbus_blink_service import ConbusBlinkService


class TestConbusBlinkIntegration:
    """Integration test cases for Conbus blink operations"""

    @staticmethod
    def _create_mock_discover_service(discovered_devices=None, success=True, error=None):
        """Helper to create a properly mocked discover service"""
        if discovered_devices is None:
            discovered_devices = ["0020044964", "0020030837"]

        mock_discover_instance = Mock()
        mock_discover_instance.__enter__ = Mock(return_value=mock_discover_instance)
        mock_discover_instance.__exit__ = Mock(return_value=False)

        mock_discover_response = ConbusDiscoverResponse(
            success=success,
            sent_telegram="<S9999999999F01D00XX>" if success else None,
            received_telegrams=[f"<R{device}F18D12>" for device in discovered_devices] if success else [],
            discovered_devices=discovered_devices,
            error=error
        )
        mock_discover_instance.send_discover_telegram.return_value = mock_discover_response

        return mock_discover_instance

    @staticmethod
    def _create_mock_conbus_response(success=True, serial_number="0020044964", error=None):
        """Helper to create a properly formed ConbusResponse"""
        mock_request = ConbusRequest(serial_number=serial_number, function_code="F05", data="D00")
        return ConbusResponse(
            success=success,
            request=mock_request,
            sent_telegram=f"<S{serial_number}F05D00FN>",
            received_telegrams=[f"<R{serial_number}F18DFA>"] if success else [],
            error=error
        )

    @patch('xp.services.conbus_blink_service.ConbusDiscoverService')
    def test_conbus_blink_all_off(self, mock_discover_service):
        """Test turning all device blinks off"""
        # Mock discover service
        mock_discover_instance = self._create_mock_discover_service()
        mock_discover_service.return_value = mock_discover_instance

        # Test the blink_all_off functionality
        service = ConbusBlinkService()

        # Mock the send_blink_telegram method to return success
        mock_blink_response = ConbusBlinkResponse(
            success=True,
            serial_number="0020044964",
            operation="off",
            system_function=SystemFunction.UNBLINK
        )

        with patch.object(service, 'send_blink_telegram', return_value=mock_blink_response):
            with service:
                response = service.blink_all('off')

        # Verify response
        assert response.success is True
        assert response.serial_number == "all"
        assert response.operation == "off"
        assert response.system_function == SystemFunction.UNBLINK
        assert response.error is None

        # Verify discover service was called
        mock_discover_instance.send_discover_telegram.assert_called_once()

    @patch('xp.services.conbus_blink_service.ConbusDiscoverService')
    def test_conbus_blink_all_on(self, mock_discover_service):
        """Test turning all device blinks on"""
        # Mock discover service
        mock_discover_instance = self._create_mock_discover_service()
        mock_discover_service.return_value = mock_discover_instance

        # Test the blink_all_on functionality
        service = ConbusBlinkService()

        # Mock the send_blink_telegram method to return success
        mock_blink_response = ConbusBlinkResponse(
            success=True,
            serial_number="0020044964",
            operation="on",
            system_function=SystemFunction.BLINK
        )

        with patch.object(service, 'send_blink_telegram', return_value=mock_blink_response):
            with service:
                response = service.blink_all('on')

        # Verify response
        assert response.success is True
        assert response.serial_number == "all"
        assert response.operation == "on"
        assert response.system_function == SystemFunction.BLINK
        assert response.error is None

        # Verify discover service was called
        mock_discover_instance.send_discover_telegram.assert_called_once()

    @patch('xp.services.conbus_blink_service.ConbusDiscoverService')
    def test_conbus_blink_connection_error(self, mock_discover_service):
        """Handle network failures"""
        # Mock discover service to fail
        mock_discover_instance = self._create_mock_discover_service(
            discovered_devices=[],
            success=False,
            error="Connection failed"
        )
        mock_discover_service.return_value = mock_discover_instance

        # Test connection error handling
        service = ConbusBlinkService()

        with service:
            response = service.blink_all('off')

        # Verify error response
        assert response.success is False
        assert response.serial_number == "all"
        assert response.operation == "off"
        assert response.system_function == SystemFunction.UNBLINK
        assert response.error == "Failed to discover devices"

        # Test with blink_all_on as well
        with service:
            response = service.blink_all('on')

        assert response.success is False
        assert response.serial_number == "all"
        assert response.operation == "on"
        assert response.system_function == SystemFunction.BLINK
        assert response.error == "Failed to discover devices"

    @patch('xp.services.conbus_blink_service.ConbusDiscoverService')
    def test_conbus_blink_invalid_response(self, mock_discover_service):
        """Handle invalid responses"""
        # Mock discover service to return no devices
        mock_discover_instance = self._create_mock_discover_service(discovered_devices=[])
        mock_discover_service.return_value = mock_discover_instance

        # Test no devices scenario
        service = ConbusBlinkService()

        with service:
            response = service.blink_all('off')

        # Verify response for no devices
        assert response.success is True  # Success because discovery worked, just no devices
        assert response.serial_number == "all"
        assert response.operation == "off"
        assert response.system_function == SystemFunction.UNBLINK
        assert response.error == "No devices discovered"

    @patch('xp.services.conbus_blink_service.ConbusDiscoverService')
    def test_conbus_blink_partial_failure(self, mock_discover_service):
        """Test scenario where some devices fail to blink"""
        # Mock discover service
        mock_discover_instance = self._create_mock_discover_service()
        mock_discover_service.return_value = mock_discover_instance

        # Test partial failure scenario
        service = ConbusBlinkService()

        # Mock send_blink_telegram to return mixed success/failure
        success_response = ConbusBlinkResponse(
            success=True,
            serial_number="0020044964",
            operation="on",
            system_function=SystemFunction.BLINK
        )
        failure_response = ConbusBlinkResponse(
            success=False,
            serial_number="0020030837",
            operation="on",
            system_function=SystemFunction.BLINK,
            error="Device timeout"
        )

        with patch.object(service, 'send_blink_telegram', side_effect=[success_response, failure_response]):
            with service:
                response = service.blink_all('on')

        # Verify partial failure response
        assert response.success is False  # Should be False because not all devices succeeded
        assert response.serial_number == "all"
        assert response.operation == "on"
        assert response.system_function == SystemFunction.BLINK
        assert response.error == "Some devices failed to blink"

    def test_conbus_blink_service_context_manager(self):
        """Test that the service works properly as a context manager"""
        service = ConbusBlinkService()

        # Test entering and exiting context manager
        with service:
            assert service is not None

        # Should not raise any exceptions

    @patch('xp.services.conbus_blink_service.ConbusDiscoverService')
    def test_conbus_blink_all_multiple_devices(self, mock_discover_service):
        """Test blinking multiple devices successfully"""
        # Mock discover service with multiple devices
        devices = ["0020044964", "0020030837", "1234567890", "9876543210"]
        mock_discover_instance = self._create_mock_discover_service(discovered_devices=devices)
        mock_discover_service.return_value = mock_discover_instance

        # Test multiple devices
        service = ConbusBlinkService()

        # Mock send_blink_telegram to always return success
        mock_blink_response = ConbusBlinkResponse(
            success=True,
            serial_number="device",
            operation="on",
            system_function=SystemFunction.BLINK
        )

        with patch.object(service, 'send_blink_telegram', return_value=mock_blink_response) as mock_send:
            with service:
                response = service.blink_all('on')

        # Verify all devices were processed
        assert response.success is True
        assert response.serial_number == "all"
        assert response.operation == "on"
        assert response.system_function == SystemFunction.BLINK
        assert response.error is None

        # Verify send_blink_telegram was called for each device
        assert mock_send.call_count == len(devices)
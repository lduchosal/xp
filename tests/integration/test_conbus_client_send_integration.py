import pytest
import threading
import time
import socket
from datetime import datetime
from src.xp.services.conbus_client_send_service import ConbusClientSendService
from src.xp.models import ConbusSendRequest, TelegramType


class MockConbusServer:
    """Mock Conbus server for integration testing"""

    def __init__(self, port=10001):
        self.port = port
        self.server_socket = None
        self.is_running = False
        self.received_messages = []
        self.response_map = {
            "<S0000000000F01D00FA>": [
                "<R0020030837F01DFM>",
                "<R0020044966F01DFK>",
                "<R0020042796F01DFN>",
            ],
            "<S0020030837F02D02FM>": ["<R0020030837F02D02XP230_V1.00.04FI>"],
            "<S0020012521F02D18FN>": ["<R0020012521F02D18+23.4C§OK>"],
            "<S0020030837F02D20FM>": ["<R0020030837F02D20+12.5V§OK>"],
            "<S0020030837F02DE2CJ>": ["<R0020030837F02DE2COUCOUFM>"],
        }

    def start(self):
        """Start the mock server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("localhost", self.port))
        self.server_socket.listen(1)
        self.is_running = True

        server_thread = threading.Thread(target=self._accept_connections, daemon=True)
        server_thread.start()

        # Give server time to start
        time.sleep(0.1)

    def stop(self):
        """Stop the mock server"""
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()

    def _accept_connections(self):
        """Accept and handle client connections"""
        while self.is_running:
            try:
                client_socket, addr = self.server_socket.accept()
                self._handle_client(client_socket)
            except (socket.error, OSError):
                break

    def _handle_client(self, client_socket):
        """Handle individual client connection"""
        try:
            client_socket.settimeout(2.0)

            while True:
                data = client_socket.recv(1024)
                if not data:
                    break

                message = data.decode("latin-1").strip()
                self.received_messages.append(message)

                # Send configured responses
                responses = self.response_map.get(message, [])
                for response in responses:
                    client_socket.send(response.encode("latin-1"))
                    time.sleep(0.01)  # Small delay between responses

        except socket.timeout:
            pass
        except Exception:
            pass
        finally:
            try:
                client_socket.close()
            except Exception:
                pass


class TestConbusClientSendIntegration:
    """Integration tests for Conbus client send functionality"""

    @pytest.fixture
    def config_file(self, tmp_path):
        """Create temporary configuration file"""
        config_file = tmp_path / "cli.yml"
        config_content = """
conbus:
  ip: localhost
  port: 10001
  timeout: 5
"""
        config_file.write_text(config_content)
        return str(config_file)

    @pytest.fixture
    def mock_server(self):
        """Create and start mock server"""
        server = MockConbusServer(port=10001)
        server.start()
        yield server
        server.stop()

    @pytest.fixture
    def client_service(self, config_file):
        """Create client service with test configuration"""
        return ConbusClientSendService(config_path=config_file)


class TestBasicConnectivity(TestConbusClientSendIntegration):
    """Test basic connectivity and configuration"""

    def test_connection_establishment(self, client_service, mock_server):
        """Test successful connection establishment"""
        result = client_service.connect()

        assert result.success is True
        assert client_service.is_connected is True
        assert "Connected to localhost:10001" in result.data["message"]

        client_service.disconnect()

    def test_connection_failure_no_server(self, client_service):
        """Test connection failure when no server is running"""
        result = client_service.connect()

        assert result.success is False
        assert "Failed to connect to localhost:10001" in result.error
        assert client_service.is_connected is False

    def test_configuration_loading(self, client_service):
        """Test that configuration is loaded correctly"""
        config = client_service.get_config()

        assert config.ip == "localhost"
        assert config.port == 10001
        assert config.timeout == 5


class TestDiscoveryTelegrams(TestConbusClientSendIntegration):
    """Test discovery telegram functionality"""

    def test_discovery_send_receive(self, client_service, mock_server):
        """Test sending discovery telegram and receiving responses"""
        with client_service:
            response = client_service.send_discovery()

        assert response.success is True
        assert response.sent_telegram == "<S0000000000F01D00FA>"
        assert len(response.received_telegrams) == 3
        assert "<R0020030837F01DFM>" in response.received_telegrams
        assert "<R0020044966F01DFK>" in response.received_telegrams
        assert "<R0020042796F01DFN>" in response.received_telegrams

        # Verify server received the message
        assert "<S0000000000F01D00FA>" in mock_server.received_messages

    def test_discovery_telegram_request_object(self, client_service, mock_server):
        """Test discovery using request object"""
        request = ConbusSendRequest(telegram_type=TelegramType.DISCOVERY)

        with client_service:
            response = client_service.send_telegram(request)

        assert response.success is True
        assert response.request.telegram_type == TelegramType.DISCOVERY
        assert len(response.received_telegrams) >= 1


class TestVersionTelegrams(TestConbusClientSendIntegration):
    """Test version request telegram functionality"""

    def test_version_request_send_receive(self, client_service, mock_server):
        """Test sending version request and receiving response"""
        with client_service:
            response = client_service.send_version_request("0020030837")

        assert response.success is True
        assert response.sent_telegram == "<S0020030837F02D02FM>"
        assert len(response.received_telegrams) == 1
        assert response.received_telegrams[0] == "<R0020030837F02D02XP230_V1.00.04FI>"

        # Verify server received the message
        assert "<S0020030837F02D02FM>" in mock_server.received_messages


class TestSensorTelegrams(TestConbusClientSendIntegration):
    """Test sensor data request telegrams"""

    def test_temperature_request(self, client_service, mock_server):
        """Test temperature sensor request"""
        with client_service:
            response = client_service.send_sensor_request(
                "0020012521", TelegramType.TEMPERATURE
            )

        assert response.success is True
        assert response.sent_telegram == "<S0020012521F02D18FN>"
        assert len(response.received_telegrams) == 1
        assert response.received_telegrams[0] == "<R0020012521F02D18+23.4C§OK>"

    def test_voltage_request(self, client_service, mock_server):
        """Test voltage sensor request"""
        with client_service:
            response = client_service.send_sensor_request(
                "0020030837", TelegramType.VOLTAGE
            )

        assert response.success is True
        assert response.sent_telegram == "<S0020030837F02D20FM>"
        assert len(response.received_telegrams) == 1
        assert response.received_telegrams[0] == "<R0020030837F02D20+12.5V§OK>"

    def test_multiple_sensor_requests(self, client_service, mock_server):
        """Test multiple sensor requests in sequence"""
        sensor_types = [TelegramType.VOLTAGE, TelegramType.TEMPERATURE]
        serial = "0020030837"

        with client_service:
            for sensor_type in sensor_types:
                if sensor_type == TelegramType.TEMPERATURE:
                    serial = "0020012521"  # Use different serial for temperature

                response = client_service.send_sensor_request(serial, sensor_type)
                assert response.success is True
                assert len(response.received_telegrams) >= 1


class TestCustomTelegrams(TestConbusClientSendIntegration):
    """Test custom telegram functionality"""

    def test_custom_telegram_send(self, client_service, mock_server):
        """Test sending custom telegram"""
        # Add custom response to mock server
        custom_telegram = "<S0020030837F02DE2CJ>"
        custom_response = "<R0020030837F02DE2COUCOUFM>"
        mock_server.response_map[custom_telegram] = [custom_response]

        with client_service:
            response = client_service.send_custom_telegram("0020030837", "02", "E2")

        assert response.success is True
        assert response.sent_telegram == custom_telegram
        assert len(response.received_telegrams) == 1
        assert response.received_telegrams[0] == custom_response


class TestErrorScenarios(TestConbusClientSendIntegration):
    """Test error scenarios and edge cases"""

    def test_server_disconnect_during_operation(self, client_service, mock_server):
        """Test handling of server disconnect during operation"""
        # Connect first
        with client_service:
            # Send first request successfully
            response1 = client_service.send_discovery()
            assert response1.success is True

            # Stop server
            mock_server.stop()
            time.sleep(0.1)

            # Try to send another request
            response2 = client_service.send_discovery()
            # This might succeed or fail depending on timing and connection state
            # The important thing is that it doesn't crash
            assert isinstance(response2.success, bool)

    def test_no_response_from_server(self, client_service):
        """Test handling when server doesn't respond"""
        # Create server that accepts connections but doesn't send responses
        server = MockConbusServer(port=10002)
        server.response_map = {}  # No responses
        server.start()

        try:
            # Update client configuration
            client_service.config.port = 10002

            with client_service:
                response = client_service.send_discovery()

            assert response.success is True  # Send should still succeed
            assert response.sent_telegram == "<S0000000000F01D00FA>"
            assert len(response.received_telegrams) == 0  # No responses

        finally:
            server.stop()


class TestConnectionStatusIntegration(TestConbusClientSendIntegration):
    """Test connection status tracking in integration scenarios"""

    def test_connection_status_lifecycle(self, client_service, mock_server):
        """Test connection status throughout connection lifecycle"""
        # Initially disconnected
        status = client_service.get_connection_status()
        assert status.connected is False
        assert status.last_activity is None

        # Connect and send telegram
        with client_service:
            client_service.connect()

            # After connection
            status = client_service.get_connection_status()
            assert status.connected is True

            # Send telegram
            response = client_service.send_discovery()
            assert response.success is True

            # Check activity was recorded
            status = client_service.get_connection_status()
            assert status.connected is True
            assert status.last_activity is not None
            assert isinstance(status.last_activity, datetime)

        # After disconnect
        status = client_service.get_connection_status()
        assert status.connected is False


class TestWorkflowIntegration(TestConbusClientSendIntegration):
    """Test complete workflow integration scenarios"""

    def test_complete_discovery_workflow(self, client_service, mock_server):
        """Test complete discovery workflow as specified"""
        with client_service:
            # Step 1: Send discovery
            discovery_response = client_service.send_discovery()
            assert discovery_response.success is True

            # Step 2: For each discovered device, request version
            discovered_devices = [
                "0020030837",  # From mock responses
                # Could extract more from actual responses
            ]

            for device_serial in discovered_devices:
                version_response = client_service.send_version_request(device_serial)
                if version_response.success:
                    assert len(version_response.received_telegrams) >= 1
                    # Could parse version info from response

    def test_sensor_monitoring_workflow(self, client_service, mock_server):
        """Test sensor data monitoring workflow"""
        device_serial = "0020012521"
        sensor_types = [TelegramType.TEMPERATURE, TelegramType.VOLTAGE]

        with client_service:
            for sensor_type in sensor_types:
                if sensor_type == TelegramType.VOLTAGE:
                    device_serial = "0020030837"  # Different device for voltage

                response = client_service.send_sensor_request(
                    device_serial, sensor_type
                )

                if response.success:
                    assert len(response.received_telegrams) >= 1
                    # Could parse sensor values from response
                    print(
                        f"Sensor {sensor_type.value} response: {response.received_telegrams}"
                    )

    def test_error_recovery_workflow(self, client_service, mock_server):
        """Test error recovery workflow"""
        with client_service:
            # First request should succeed
            response1 = client_service.send_discovery()
            assert response1.success is True

            # Simulate network issue by stopping server briefly
            mock_server.stop()
            time.sleep(0.1)

            # This request might fail
            client_service.send_discovery()

            # Restart server
            mock_server.start()
            time.sleep(0.1)

            # Reconnect and try again
            client_service.disconnect()
            client_service.send_discovery()
            # Should eventually succeed with retry logic

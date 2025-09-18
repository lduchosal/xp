import pytest
import threading
import time
import socket
from datetime import datetime
from src.xp.services.conbus_datapoint_service import ConbusDatapointService
from src.xp.models import ConbusDatapointRequest
from xp.models import DatapointTypeName


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
        return ConbusDatapointService(config_path=config_file)


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
            response = client_service.datapoint_request(
                "0020012521", DatapointTypeName.TEMPERATURE
            )

        assert response.success is True
        assert response.sent_telegram == "<S0020012521F02D18FN>"
        assert len(response.received_telegrams) == 1
        assert response.received_telegrams[0] == "<R0020012521F02D18+23.4C§OK>"

    def test_voltage_request(self, client_service, mock_server):
        """Test voltage sensor request"""
        with client_service:
            response = client_service.datapoint_request(
                "0020030837", DatapointTypeName.VOLTAGE
            )

        assert response.success is True
        assert response.sent_telegram == "<S0020030837F02D20FM>"
        assert len(response.received_telegrams) == 1
        assert response.received_telegrams[0] == "<R0020030837F02D20+12.5V§OK>"

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


class TestConnectionStatusIntegration(TestConbusClientSendIntegration):
    """Test connection status tracking in integration scenarios"""

class TestWorkflowIntegration(TestConbusClientSendIntegration):
    """Test complete workflow integration scenarios"""

    def test_sensor_monitoring_workflow(self, client_service, mock_server):
        """Test sensor data monitoring workflow"""
        device_serial = "0020012521"
        sensor_types = [DatapointTypeName.TEMPERATURE, DatapointTypeName.VOLTAGE]

        with client_service:
            for sensor_type in sensor_types:
                if sensor_type == DatapointTypeName.VOLTAGE:
                    device_serial = "0020030837"  # Different device for voltage

                response = client_service.datapoint_request(
                    device_serial, sensor_type
                )

                if response.success:
                    assert len(response.received_telegrams) >= 1
                    # Could parse sensor values from response
                    print(
                        f"Sensor {sensor_type.value} response: {response.received_telegrams}"
                    )

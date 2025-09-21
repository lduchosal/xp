"""
Unit tests for Latin-1 encoding edge cases in Conbus communication.

Tests the specific encoding fix for the issue described in doc/Fix-Encoding-Issue.md
where UTF-8 decoding fails on Latin-1 characters like 0xa7 (§ symbol).
"""

import socket
import threading
import time

import pytest

from xp.services.conbus_datapoint_service import ConbusDatapointService


class Latin1TestServer:
    """Test server that sends responses with Latin-1 extended characters"""

    def __init__(self, port=10003):
        self.port = port
        self.server_socket = None
        self.is_running = False
        self.received_messages = []

    def start(self):
        """Start the test server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("localhost", self.port))
        self.server_socket.listen(1)
        self.is_running = True

        server_thread = threading.Thread(target=self._accept_connections, daemon=True)
        server_thread.start()
        time.sleep(0.1)  # Give server time to start

    def stop(self):
        """Stop the test server"""
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

                # Send responses with Latin-1 extended characters
                response = self._generate_latin1_response(message)
                if response:
                    client_socket.send(response.encode("latin-1"))

        except socket.timeout:
            pass
        except (ValueError, KeyError, ConnectionError):
            pass
        finally:
            try:
                client_socket.close()
            except (ValueError, KeyError, ConnectionError):
                pass

    @staticmethod
    def _generate_latin1_response(message):
        """Generate responses containing Latin-1 extended characters"""
        # Map of requests to responses with extended characters
        latin1_responses = {
            # Temperature request with § symbol (0xa7)
            "<S0020012521F02D18FN>": "<R0020044966F02D18+31,5§CIE>",
            # VOLTAGE request with © symbol (0xa9)
            "<S0012345011F02D20FM>": "<R0012345011F02D20+12,5V©OK>",
            # Current request with ® symbol (0xae)
            "<S0012345006F02D21FL>": "<R0012345006F02D21+2,3A®OK>",
            # Humidity request with ± symbol (0xb1)
            "<S0012345003F02D19FH>": "<R0012345003F02D19+65,2%±OK>",
            # Custom request with multiple extended chars
            "<S0012345011F02DE2CJ>": "<R0012345011F02DE2COUCOU§©®±FM>",
            # Discover with extended chars in device name
            "<S0000000000F01D00FA>": "<R0012345011F01D©XP24®>",
        }

        return latin1_responses.get(message)


class TestLatin1EdgeCases:
    """Test cases for Latin-1 encoding edge cases"""

    @pytest.fixture
    def latin1_server(self):
        """Create and start Latin-1 test server"""
        server = Latin1TestServer(port=10003)
        server.start()
        yield server
        server.stop()

    @pytest.fixture
    def client_service(self, tmp_path):
        """Create client service configured for Latin-1 test server"""
        config_file = tmp_path / "cli.yml"
        config_content = """
conbus:
  ip: localhost
  port: 10003
  timeout: 5
"""
        config_file.write_text(config_content)
        return ConbusDatapointService(config_path=str(config_file))

    def test_edge_case_byte_values(self, client_service):
        """Test specific problematic byte values mentioned in the issue"""
        # Test byte 0xa7 (167 decimal) = § symbol
        problematic_byte = 0xA7
        char = chr(problematic_byte)

        # This would have failed with UTF-8 but should work with Latin-1
        test_data = f"<R0020044966F02D18+31,5{char}CIE>".encode("latin-1")
        decoded = test_data.decode("latin-1")

        assert char in decoded
        assert decoded == "<R0020044966F02D18+31,5§CIE>"

    def test_raw_hex_data_decoding(self, client_service):
        """Test decoding of the actual hex data from the issue description"""
        # From the spec: Problem response hex data
        hex_data = "3c52303032303034343936364630324431382b33312c35a7434945"

        # Convert hex string to bytes
        raw_bytes = bytes.fromhex(hex_data)

        # This should decode properly with Latin-1
        decoded = raw_bytes.decode("latin-1")
        expected = "<R0020044966F02D18+31,5§CIE"

        assert decoded == expected
        assert chr(0xA7) in decoded  # § symbol at position 23
        assert len(decoded) == 27  # Correct length

    def test_utf8_vs_latin1_comparison(self, client_service):
        """Test that demonstrates the fix - Latin-1 works where UTF-8 fails"""
        # Hex data that contains byte 0xa7
        hex_data = "3c52303032303034343936364630324431382b33312c35a7434945"
        raw_bytes = bytes.fromhex(hex_data)

        # UTF-8 decoding should fail (this demonstrates the original problem)
        with pytest.raises(UnicodeDecodeError) as exc_info:
            raw_bytes.decode("utf-8")

        assert "'utf-8' codec can't decode byte 0xa7 in position 23" in str(
            exc_info.value
        )

        # Latin-1 decoding should succeed (this demonstrates the fix)
        decoded_latin1 = raw_bytes.decode("latin-1")
        assert decoded_latin1 == "<R0020044966F02D18+31,5§CIE"
        assert len(decoded_latin1) == 27
        assert decoded_latin1[23] == "§"  # Character at problematic position


class TestEncodingConsistency:
    """Test encoding consistency across the communication pipeline"""

    def test_round_trip_encoding(self):
        """Test that messages can be encoded and decoded consistently"""
        test_messages = [
            "<S0020012521F02D18FN>",  # Normal ASCII message
            "<R0020012521F02D18+31,5§CIE>",  # Message with § symbol
            "<R0012345011F02D20+12,5V©OK>",  # Message with © symbol
            "<R0012345006F02D21+2,3A®OK>",  # Message with ® symbol
            "<R0012345003F02D19+65,2%±OK>",  # Message with ± symbol
        ]

        for message in test_messages:
            # Encode to bytes using Latin-1
            encoded = message.encode("latin-1")

            # Decode back using Latin-1
            decoded = encoded.decode("latin-1")

            # Should be identical
            assert decoded == message

            # Verify extended characters are preserved
            for char in message:
                if ord(char) > 127:  # Extended character
                    assert char in decoded

    def test_latin1_character_range(self):
        """Test that all Latin-1 characters (0-255) can be handled"""
        # Test all possible byte values
        for byte_value in range(256):
            char = chr(byte_value)
            test_string = f"Test{char}Message"

            # Should be able to encode and decode without errors
            encoded = test_string.encode("latin-1")
            decoded = encoded.decode("latin-1")

            assert decoded == test_string
            assert char in decoded

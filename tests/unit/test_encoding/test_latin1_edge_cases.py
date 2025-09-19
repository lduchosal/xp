"""
Unit tests for Latin-1 encoding edge cases in Conbus communication.

Tests the specific encoding fix for the issue described in doc/Fix-Encoding-Issue.md
where UTF-8 decoding fails on Latin-1 characters like 0xa7 (§ symbol).
"""

import pytest
import socket
import threading
import time
from xp.services.conbus_datapoint_service import ConbusDatapointService
from xp.models import DatapointTypeName


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
        except Exception:
            pass
        finally:
            try:
                client_socket.close()
            except Exception:
                pass

    def _generate_latin1_response(self, message):
        """Generate responses containing Latin-1 extended characters"""
        # Map of requests to responses with extended characters
        latin1_responses = {
            # Temperature request with § symbol (0xa7)
            "<S0020012521F02D18FN>": "<R0020012521F02D18+31,5§CIE>",
            # Voltage request with © symbol (0xa9)
            "<S0020030837F02D20FM>": "<R0020030837F02D20+12,5V©OK>",
            # Current request with ® symbol (0xae)
            "<S0020044966F02D21FL>": "<R0020044966F02D21+2,3A®OK>",
            # Humidity request with ± symbol (0xb1)
            "<S0020042796F02D19FH>": "<R0020042796F02D19+65,2%±OK>",
            # Custom request with multiple extended chars
            "<S0020030837F02DE2CJ>": "<R0020030837F02DE2COUCOU§©®±FM>",
            # Discovery with extended chars in device name
            "<S0000000000F01D00FA>": "<R0020030837F01D©XP24®>",
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

    def test_section_symbol_0xa7(self, client_service, latin1_server):
        """Test handling of § symbol (byte 0xa7) in temperature response"""
        with client_service:
            response = client_service.datapoint_request(
                "0020012521", DatapointTypeName.TEMPERATURE
            )

        assert response.success is True
        assert response.sent_telegram == "<S0020012521F02D18FN>"
        assert len(response.received_telegrams) == 1
        # This should contain the § symbol without UTF-8 decode errors
        assert response.received_telegrams[0] == "<R0020012521F02D18+31,5§CIE>"
        assert "§" in response.received_telegrams[0]

    def test_copyright_symbol_0xa9(self, client_service, latin1_server):
        """Test handling of © symbol (byte 0xa9) in voltage response"""
        with client_service:
            response = client_service.datapoint_request(
                "0020030837", DatapointTypeName.VOLTAGE
            )

        assert response.success is True
        assert response.sent_telegram == "<S0020030837F02D20FM>"
        assert len(response.received_telegrams) == 1
        assert response.received_telegrams[0] == "<R0020030837F02D20+12,5V©OK>"
        assert "©" in response.received_telegrams[0]

    def test_registered_symbol_0xae(self, client_service, latin1_server):
        """Test handling of ® symbol (byte 0xae) in current response"""
        with client_service:
            response = client_service.datapoint_request(
                "0020044966", DatapointTypeName.CURRENT
            )

        assert response.success is True
        assert response.sent_telegram == "<S0020044966F02D17FO>"
        assert len(response.received_telegrams) == 1
        assert response.received_telegrams[0] == "<R0020044966F02D21+2,3A®OK>"
        assert "®" in response.received_telegrams[0]

    def test_plus_minus_symbol_0xb1(self, client_service, latin1_server):
        """Test handling of ± symbol (byte 0xb1) in humidity response"""
        with client_service:
            response = client_service.datapoint_request(
                "0020042796", DatapointTypeName.HUMIDITY
            )

        assert response.sent_telegram == "<S0020042796F02D19FH>"
        assert response.success is True
        assert len(response.received_telegrams) == 1
        assert response.received_telegrams[0] == "<R0020042796F02D19+65,2%±OK>"
        assert "±" in response.received_telegrams[0]

    def test_multiple_extended_characters(self, client_service, latin1_server):
        """Test handling of multiple Latin-1 extended characters in one message"""
        with client_service:
            response = client_service.send_custom_telegram("0020030837", "02", "E2")

        assert response.success is True
        assert response.sent_telegram == "<S0020030837F02DE2CJ>"
        assert len(response.received_telegrams) == 1
        expected = "<R0020030837F02DE2COUCOU§©®±FM>"
        assert response.received_telegrams[0] == expected
        # Verify all extended characters are present
        assert "§" in response.received_telegrams[0]
        assert "©" in response.received_telegrams[0]
        assert "®" in response.received_telegrams[0]
        assert "±" in response.received_telegrams[0]

    def test_all_latin1_extended_chars(self, client_service, latin1_server):
        """Test a comprehensive range of Latin-1 extended characters (128-255)"""
        # Create a test message with various Latin-1 extended characters
        extended_chars = [
            0x80,
            0x81,
            0x82,
            0x83,
            0x84,
            0x85,
            0x86,
            0x87,  # 128-135
            0xA0,
            0xA1,
            0xA2,
            0xA3,
            0xA4,
            0xA5,
            0xA6,
            0xA7,  # 160-167
            0xA8,
            0xA9,
            0xAA,
            0xAB,
            0xAC,
            0xAD,
            0xAE,
            0xAF,  # 168-175
            0xB0,
            0xB1,
            0xB2,
            0xB3,
            0xB4,
            0xB5,
            0xB6,
            0xB7,  # 176-183
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC4,
            0xC5,
            0xC6,
            0xC7,  # 192-199
            0xE0,
            0xE1,
            0xE2,
            0xE3,
            0xE4,
            0xE5,
            0xE6,
            0xE7,  # 224-231
            0xF0,
            0xF1,
            0xF2,
            0xF3,
            0xF4,
            0xF5,
            0xF6,
            0xF7,  # 240-247
        ]

        # Test that each extended character can be decoded without errors
        for char_code in extended_chars:
            char = chr(char_code)
            test_message = f"<R0020030837F02D20+12,5V{char}OK>"

            # This should not raise a UnicodeDecodeError
            decoded = test_message.encode("latin-1").decode("latin-1")
            assert decoded == test_message
            assert char in decoded

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
            "<R0020030837F02D20+12,5V©OK>",  # Message with © symbol
            "<R0020044966F02D21+2,3A®OK>",  # Message with ® symbol
            "<R0020042796F02D19+65,2%±OK>",  # Message with ± symbol
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

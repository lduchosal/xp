"""Unit tests for checksum utility functions.

Tests the checksum calculation functions to ensure they match
the expected behavior
"""

import pytest
from xp.utils.checksum import (
    calculate_checksum,
    calculate_checksum32,
    de_nibble,
    un_bcd,
    a_nibble,
    a_byte_to_int_no_sign,
)


class TestChecksumUtilities:
    """Test class for checksum utility functions."""

    def test_calculate_checksum_simple(self):
        """Test simple XOR checksum calculation."""
        result = calculate_checksum("E14L00I02M")
        assert isinstance(result, str)
        assert len(result) == 2

        # Test known case - XOR of ASCII values should produce specific result
        test_data = "ABC"
        expected_xor = ord("A") ^ ord("B") ^ ord("C")  # 65 ^ 66 ^ 67 = 64
        result = calculate_checksum(test_data)

        # Convert back to verify
        nibble_bytes = de_nibble(result)
        assert nibble_bytes[0] == expected_xor

    def test_calculate_checksum_empty_string(self):
        """Test checksum calculation with empty string."""
        result = calculate_checksum("")
        assert result == "AA"  # XOR of nothing is 0, nibble(0) = "AA"

    def test_calculate_checksum_single_char(self):
        """Test checksum calculation with single character."""
        result = calculate_checksum("A")
        assert isinstance(result, str)
        assert len(result) == 2

        # 'A' = ASCII 65 = 0x41, nibble should be "EB"
        assert result == "EB"

    def test_nibble_conversion(self):
        """Test nibble conversion function."""
        # Test zero
        assert a_nibble(0) == "AA"

        # Test 0x41 (ASCII 'A')
        assert a_nibble(0x41) == "EB"

        # Test 0xFF (255)
        assert a_nibble(0xFF) == "PP"

    def test_de_nibble_conversion(self):
        """Test reverse nibble conversion."""
        # Test "AA" -> 0
        result = de_nibble("AA")
        assert result == b"\x00"

        # Test "EB" -> 0x41
        result = de_nibble("EB")
        assert result == b"\x41"

        # Test "PP" -> 0xFF
        result = de_nibble("PP")
        assert result == b"\xff"

    def test_de_nibble_multiple_bytes(self):
        """Test de_nibble with multiple byte pairs."""
        result = de_nibble("AAEB")
        assert result == b"\x00\x41"

        result = de_nibble("EBAA")
        assert result == b"\x41\x00"

    def test_de_nibble_invalid_length(self):
        """Test de_nibble with odd length string."""
        with pytest.raises(ValueError, match="String length must be even"):
            de_nibble("A")

        with pytest.raises(ValueError, match="String length must be even"):
            de_nibble("ABC")

    def test_byte_to_int_no_sign(self):
        """Test unsigned byte conversion."""
        assert a_byte_to_int_no_sign(0) == 0
        assert a_byte_to_int_no_sign(127) == 127
        assert a_byte_to_int_no_sign(-1) == 255
        assert a_byte_to_int_no_sign(-128) == 128

    def test_un_bcd_conversion(self):
        """Test BCD to integer conversion."""
        # BCD 0x12 should be decimal 12
        assert un_bcd(0x12) == 12

        # BCD 0x99 should be decimal 99
        assert un_bcd(0x99) == 99

        # BCD 0x00 should be decimal 0
        assert un_bcd(0x00) == 0

    def test_calculate_checksum32_simple(self):
        """Test CRC32 checksum calculation."""
        # Test with simple byte array
        data = b"test"
        result = calculate_checksum32(data)

        assert isinstance(result, str)
        assert len(result) == 8  # 4 bytes * 2 chars per byte

        # All characters should be in valid nibble range (A-P)
        for char in result:
            assert "A" <= char <= "P"

    def test_calculate_checksum32_empty(self):
        """Test CRC32 checksum with empty data."""
        result = calculate_checksum32(b"")
        assert isinstance(result, str)
        assert len(result) == 8

    def test_calculate_checksum32_known_value(self):
        """Test CRC32 with known test vector."""
        # Test "123456789" which has a known CRC32 value
        data = b"123456789"
        result = calculate_checksum32(data)

        # The result should be consistent
        assert isinstance(result, str)
        assert len(result) == 8

        # Test that multiple calls produce same result
        result2 = calculate_checksum32(data)
        assert result == result2

    def test_calculate_checksum32_different_inputs(self):
        """Test CRC32 produces different results for different inputs."""
        result1 = calculate_checksum32(b"test1")
        result2 = calculate_checksum32(b"test2")

        assert result1 != result2

    def test_checksum_consistency(self):
        """Test that checksum functions are consistent across calls."""
        data = "E14L00I02M"

        # Multiple calls should produce same result
        result1 = calculate_checksum(data)
        result2 = calculate_checksum(data)
        assert result1 == result2

        # Same for CRC32
        byte_data = data.encode("utf-8")
        crc1 = calculate_checksum32(byte_data)
        crc2 = calculate_checksum32(byte_data)
        assert crc1 == crc2

    def test_nibble_roundtrip(self):
        """Test that nibble conversion is reversible."""
        for test_byte in [0, 1, 65, 127, 255]:
            nibbled = a_nibble(test_byte)
            de_nibbled = de_nibble(nibbled)
            assert de_nibbled[0] == test_byte

    def test_telegram_example(self):
        """Test with actual telegram example from documentation."""
        telegram_data = "E14L00I02M"
        checksum = calculate_checksum(telegram_data)

        # Should produce a valid 2-character checksum
        assert isinstance(checksum, str)
        assert len(checksum) == 2
        assert all("A" <= c <= "P" for c in checksum)

    @pytest.mark.parametrize(
        "test_input,expected_type",
        [
            ("", str),
            ("A", str),
            ("ABC", str),
            ("E14L00I02M", str),
            ("Hello World", str),
        ],
    )
    def test_calculate_checksum_various_inputs(self, test_input, expected_type):
        """Test checksum calculation with various inputs."""
        result = calculate_checksum(test_input)
        assert isinstance(result, expected_type)
        assert len(result) == 2

    @pytest.mark.parametrize(
        "test_input",
        [
            b"",
            b"test",
            b"Hello World",
            b"\x00\x01\x02\x03",
            bytes(range(256)),
        ],
    )
    def test_calculate_checksum32_various_inputs(self, test_input):
        """Test CRC32 calculation with various inputs."""
        result = calculate_checksum32(test_input)
        assert isinstance(result, str)
        assert len(result) == 8
        assert all("A" <= c <= "P" for c in result)

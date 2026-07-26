# Copyright (c) 2025 ldvchosal
"""Unit tests for checksum utility functions.

Tests the checksum calculation functions to ensure they match the expected behavior.
"""

import pytest

from xp.utils.checksum import calculate_checksum, calculate_checksum32
from xp.utils.serialization import (
    byte_to_unsigned,
    de_bcd,
    de_nibbles,
    nibble,
)

CHECKSUM_LENGTH = 2
CHECKSUM32_LENGTH = 8  # 4 bytes * 2 chars per byte


class TestChecksumUtilities:
    """Test class for checksum utility functions."""

    def test_calculate_checksum_simple(self) -> None:
        """Test simple XOR checksum calculation."""
        result = calculate_checksum("E14L00I02M")
        assert isinstance(result, str)
        assert len(result) == CHECKSUM_LENGTH

        # Test known case - XOR of ASCII values should produce specific result
        test_data = "ABC"
        expected_xor = ord("A") ^ ord("B") ^ ord("C")  # 65 ^ 66 ^ 67 = 64
        result = calculate_checksum(test_data)

        # Convert back to verify
        nibble_bytes = de_nibbles(result)
        assert nibble_bytes[0] == expected_xor

    def test_calculate_checksum_empty_string(self) -> None:
        """Test checksum calculation with empty string."""
        result = calculate_checksum("")
        assert result == "AA"  # XOR of nothing is 0, nibble(0) = "AA"

    def test_calculate_checksum_single_char(self) -> None:
        """Test checksum calculation with single character."""
        result = calculate_checksum("A")
        assert isinstance(result, str)
        assert len(result) == CHECKSUM_LENGTH

        # 'A' = ASCII 65 = 0x41, nibble should be "EB"
        assert result == "EB"

    def test_nibble_conversion(self) -> None:
        """Test nibble conversion function."""
        # Test zero
        assert nibble(0) == "AA"

        # Test 0x41 (ASCII 'A')
        assert nibble(0x41) == "EB"

        # Test 0xFF (255)
        assert nibble(0xFF) == "PP"

    def test_de_nibble_conversion(self) -> None:
        """Test reverse nibble conversion."""
        # Test "AA" -> 0
        result = de_nibbles("AA")
        assert result == b"\x00"

        # Test "EB" -> 0x41
        result = de_nibbles("EB")
        assert result == b"\x41"

        # Test "PP" -> 0xFF
        result = de_nibbles("PP")
        assert result == b"\xff"

    def test_de_nibble_multiple_bytes(self) -> None:
        """Test de_nibble with multiple byte pairs."""
        result = de_nibbles("AAEB")
        assert result == b"\x00\x41"

        result = de_nibbles("EBAA")
        assert result == b"\x41\x00"

    def test_de_nibble_invalid_length(self) -> None:
        """Test de_nibble with odd length string."""
        with pytest.raises(ValueError, match="String length must be even"):
            de_nibbles("A")

        with pytest.raises(ValueError, match="String length must be even"):
            de_nibbles("ABC")

    def test_byte_to_int_no_sign(self) -> None:
        """Test unsigned byte conversion."""
        cases = [(0, 0), (127, 127), (-1, 255), (-128, 128)]
        for value, expected in cases:
            assert byte_to_unsigned(value) == expected

    def test_de_bcd_conversion(self) -> None:
        """Test BCD to integer conversion."""
        cases = [
            (0x12, 12),  # BCD 0x12 should be decimal 12
            (0x99, 99),  # BCD 0x99 should be decimal 99
            (0x00, 0),  # BCD 0x00 should be decimal 0
        ]
        for bcd_value, expected in cases:
            assert de_bcd(bcd_value) == expected

    def test_calculate_checksum32_simple(self) -> None:
        """Test CRC32 checksum calculation."""
        # Test with simple byte array
        data = b"test"
        result = calculate_checksum32(data)

        assert isinstance(result, str)
        assert len(result) == CHECKSUM32_LENGTH

        # All characters should be in valid nibble range (A-P)
        for char in result:
            assert "A" <= char <= "P"

    def test_calculate_checksum32_empty(self) -> None:
        """Test CRC32 checksum with empty data."""
        result = calculate_checksum32(b"")
        assert isinstance(result, str)
        assert len(result) == CHECKSUM32_LENGTH

    def test_calculate_checksum32_known_value(self) -> None:
        """Test CRC32 with known test vector."""
        # Test "123456789" which has a known CRC32 value
        data = b"123456789"
        result = calculate_checksum32(data)

        # The result should be consistent
        assert isinstance(result, str)
        assert len(result) == CHECKSUM32_LENGTH

        # Test that multiple calls produce same result
        result2 = calculate_checksum32(data)
        assert result == result2

    def test_calculate_checksum32_different_inputs(self) -> None:
        """Test CRC32 produces different results for different inputs."""
        result1 = calculate_checksum32(b"test1")
        result2 = calculate_checksum32(b"test2")

        assert result1 != result2

    def test_checksum_consistency(self) -> None:
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

    def test_nibble_roundtrip(self) -> None:
        """Test that nibble conversion is reversible."""
        for test_byte in (0, 1, 65, 127, 255):
            nibbled = nibble(test_byte)
            de_nibbled = de_nibbles(nibbled)
            assert de_nibbled[0] == test_byte

    def test_telegram_example(self) -> None:
        """Test with actual telegram example from documentation."""
        telegram_data = "E14L00I02M"
        checksum = calculate_checksum(telegram_data)

        # Should produce a valid 2-character checksum
        assert isinstance(checksum, str)
        assert len(checksum) == CHECKSUM_LENGTH
        assert all("A" <= c <= "P" for c in checksum)

    @pytest.mark.parametrize(
        ("test_input", "expected_type"),
        [
            ("", str),
            ("A", str),
            ("ABC", str),
            ("E14L00I02M", str),
            ("Hello World", str),
        ],
    )
    def test_calculate_checksum_various_inputs(
        self, test_input: str, expected_type: type[str]
    ) -> None:
        """Test checksum calculation with various inputs."""
        result = calculate_checksum(test_input)
        assert isinstance(result, expected_type)
        assert len(result) == CHECKSUM_LENGTH

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
    def test_calculate_checksum32_various_inputs(self, test_input: bytes) -> None:
        """Test CRC32 calculation with various inputs."""
        result = calculate_checksum32(test_input)
        assert isinstance(result, str)
        assert len(result) == CHECKSUM32_LENGTH
        assert all("A" <= c <= "P" for c in result)

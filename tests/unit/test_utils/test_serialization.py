# Copyright (c) 2025 ldvchosal
"""Unit tests for serialization utilities."""

from xp.utils.serialization import (
    bits_to_byte,
    byte_to_bits,
    byte_to_unsigned,
    de_bcd,
    lower3,
    to_bcd,
    upper5,
)


class TestBCDOperations:
    """Test BCD encoding/decoding operations."""

    def test_de_bcd_valid_values(self) -> None:
        """Test BCD decoding with valid values."""
        cases = [
            (0x00, 0),
            (0x01, 1),
            (0x09, 9),
            (0x10, 10),
            (0x15, 15),
            (0x25, 25),
            (0x99, 99),
        ]
        for bcd_value, expected in cases:
            assert de_bcd(bcd_value) == expected

    def test_to_bcd_valid_values(self) -> None:
        """Test BCD encoding with valid values."""
        cases = [
            (0, 0x00),
            (1, 0x01),
            (9, 0x09),
            (10, 0x10),
            (15, 0x15),
            (25, 0x25),
            (99, 0x99),
        ]
        for value, expected in cases:
            assert to_bcd(value) == expected

    def test_bcd_roundtrip(self) -> None:
        """Test BCD encode/decode roundtrip."""
        test_values = [0, 1, 5, 9, 10, 15, 25, 50, 99]
        for value in test_values:
            encoded = to_bcd(value)
            decoded = de_bcd(encoded)
            assert decoded == value

    def test_to_bcd_edge_cases(self) -> None:
        """Test BCD encoding edge cases."""
        # Values >= 100 should be handled gracefully
        cases = [
            (100, 0x00),  # (100 // 10) % 10 = 0, 100 % 10 = 0
            (123, 0x23),  # (123 // 10) % 10 = 2, 123 % 10 = 3
        ]
        for value, expected in cases:
            assert to_bcd(value) == expected


class TestBitOperations:
    """Test bit manipulation operations."""

    def test_lower3_extraction(self) -> None:
        """Test extraction of lower 3 bits."""
        cases = [
            (0b00000000, 0b000),
            (0b00000001, 0b001),
            (0b00000111, 0b111),
            (0b11110111, 0b111),
            (0b11111000, 0b000),
        ]
        for byte_value, expected in cases:
            assert lower3(byte_value) == expected

    def test_upper5_extraction(self) -> None:
        """Test extraction of upper 5 bits."""
        cases = [
            (0b00000000, 0b00000),
            (0b11111000, 0b11111),
            (0b10000000, 0b10000),
            (0b11110111, 0b11110),
            (0b00000111, 0b00000),
        ]
        for byte_value, expected in cases:
            assert upper5(byte_value) == expected

    def test_combined_bit_operations(self) -> None:
        """Test combining upper5 and lower3 operations."""
        # Test that a byte can be reconstructed from its parts
        test_byte = 0b11010101
        lower = lower3(test_byte)  # 0b101
        upper = upper5(test_byte)  # 0b11010
        reconstructed = (upper << 3) | lower
        assert reconstructed == test_byte


class TestByteToBits:
    """Test byte to bits conversion."""

    def test_byte_to_bits_all_zeros(self) -> None:
        """Test conversion of zero byte."""
        result = byte_to_bits(0x00)
        expected = [False] * 8
        assert result == expected

    def test_byte_to_bits_all_ones(self) -> None:
        """Test conversion of all-ones byte."""
        result = byte_to_bits(0xFF)
        expected = [True] * 8
        assert result == expected

    def test_byte_to_bits_pattern(self) -> None:
        """Test conversion of specific bit patterns."""
        # 0b10101010 = 0xAA
        result = byte_to_bits(0xAA)
        expected = [False, True, False, True, False, True, False, True]
        assert result == expected

        # 0b01010101 = 0x55
        result = byte_to_bits(0x55)
        expected = [True, False, True, False, True, False, True, False]
        assert result == expected

    def test_byte_to_bits_single_bit(self) -> None:
        """Test conversion with single bits set."""
        for i in range(8):
            byte_val = 1 << i
            result = byte_to_bits(byte_val)
            expected = [False] * 8
            expected[i] = True
            assert result == expected


class TestBitsToByte:
    """Test bits to byte conversion."""

    def test_bits_to_byte_all_false(self) -> None:
        """Test conversion of all-false bits."""
        bits = [False] * 8
        result = bits_to_byte(bits)
        assert result == 0

    def test_bits_to_byte_all_true(self) -> None:
        """Test conversion of all-true bits."""
        bits = [True] * 8
        result = bits_to_byte(bits)
        expected = 0xFF
        assert result == expected

    def test_bits_to_byte_pattern(self) -> None:
        """Test conversion of specific bit patterns."""
        # [False, True, False, True, False, True, False, True] = 0xAA
        bits = [False, True, False, True, False, True, False, True]
        result = bits_to_byte(bits)
        expected = 0xAA
        assert result == expected

        # [True, False, True, False, True, False, True, False] = 0x55
        bits = [True, False, True, False, True, False, True, False]
        result = bits_to_byte(bits)
        expected = 0x55
        assert result == expected

    def test_bits_to_byte_single_bit(self) -> None:
        """Test conversion with single bits set."""
        for i in range(8):
            bits = [False] * 8
            bits[i] = True
            result = bits_to_byte(bits)
            expected = 1 << i
            assert result == expected

    def test_bits_to_byte_truncation(self) -> None:
        """Test that extra bits beyond 8 are ignored."""
        bits = [True] * 12  # More than 8 bits
        result = bits_to_byte(bits)
        expected = 0xFF  # Only first 8 bits should be used
        assert result == expected

    def test_bits_to_byte_short_list(self) -> None:
        """Test conversion with fewer than 8 bits."""
        bits = [True, False, True]  # Only 3 bits
        result = bits_to_byte(bits)
        # Should treat missing bits as False
        expected = 0b00000101  # 5
        assert result == expected


class TestBitsRoundtrip:
    """Test roundtrip conversion between bytes and bits."""

    def test_byte_bits_roundtrip(self) -> None:
        """Test that byte->bits->byte conversion is lossless."""
        test_values = [0x00, 0xFF, 0xAA, 0x55, 0x0F, 0xF0, 0x33, 0xCC]
        for byte_val in test_values:
            bits = byte_to_bits(byte_val)
            reconstructed = bits_to_byte(bits)
            assert reconstructed == byte_val

    def test_bits_byte_roundtrip(self) -> None:
        """Test that bits->byte->bits conversion is lossless."""
        test_bits = [
            [False] * 8,
            [True] * 8,
            [True, False, True, False, True, False, True, False],
            [False, True, False, True, False, True, False, True],
        ]

        for bits in test_bits:
            byte_val = bits_to_byte(bits)
            reconstructed = byte_to_bits(byte_val)
            assert reconstructed == bits


class TestLegacyBCDOperations:
    """Test legacy BCD operations moved from checksum.py."""

    def test_a_byte_to_int_no_sign_positive(self) -> None:
        """Test conversion of positive bytes."""
        cases = [(0, 0), (127, 127), (255, 255)]
        for value, expected in cases:
            assert byte_to_unsigned(value) == expected

    def test_a_byte_to_int_no_sign_negative(self) -> None:
        """Test conversion of negative bytes."""
        cases = [(-1, 255), (-128, 128), (-256, 0)]
        for value, expected in cases:
            assert byte_to_unsigned(value) == expected

    def test_de_bcd_with_signed_conversion(self) -> None:
        """Test de_bcd works correctly with signed byte conversion."""
        # Test that de_bcd handles signed bytes correctly via a_byte_to_int_no_sign
        cases = [
            (-1, 165),  # -1 -> 255 -> 0xFF -> 15*10+15 = 165
            # More realistic BCD test with potential sign issues
            (0x12, 12),
            (0x34, 34),
        ]
        for value, expected in cases:
            assert de_bcd(value) == expected


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_negative_byte_values(self) -> None:
        """Test handling of negative values (should be treated as unsigned)."""
        # These should work with Python's bitwise operations
        expected_lower3 = 0b111  # -1 as unsigned is 0xFF, lower 3 bits are 111
        expected_upper5 = 0b11111  # -1 as unsigned is 0xFF, upper 5 bits are 11111
        assert lower3(-1) == expected_lower3
        assert upper5(-1) == expected_upper5

    def test_large_byte_values(self) -> None:
        """Test handling of values larger than 255."""
        # These should work due to Python's automatic masking
        assert lower3(256) == 0  # 256 & 0x07 = 0
        assert upper5(256) == 0  # (256 & 0xF8) >> 3 = 0

    def test_empty_bits_list(self) -> None:
        """Test conversion of empty bits list."""
        result = bits_to_byte([])
        assert result == 0

    def test_none_bits_in_list(self) -> None:
        """Test that non-boolean values are handled appropriately."""
        # This should work with Python's truthiness
        bits = [
            bool(1),
            bool(0),
            bool(1),
            bool(0),
            bool(1),
            bool(0),
            bool(1),
            bool(0),
        ]  # Truthy/falsy values
        result = bits_to_byte(bits)
        expected = 0x55  # 1s become True, 0s become False
        assert result == expected

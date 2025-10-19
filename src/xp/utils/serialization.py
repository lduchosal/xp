"""Binary serialization utility functions.

This module provides common binary manipulation functions used across
the XP protocol serializers for consistent data encoding/decoding.
"""

from typing import List

# BCD and bit manipulation constants
UPPER4 = 240  # 0xF0
LOWER4 = 15  # 0x0F
LOWER3 = 7  # 0x07
UPPER5 = 248  # 0xF8


def de_bcd(byte_val: int) -> int:
    """Convert BCD byte to decimal.

    Args:
        byte_val: BCD encoded byte

    Returns:
        Decimal value
    """
    return ((UPPER4 & byte_val) >> 4) * 10 + (LOWER4 & byte_val)


def to_bcd(decimal_val: int) -> int:
    """Convert decimal to BCD byte.

    Args:
        decimal_val: Decimal value to convert

    Returns:
        BCD encoded byte
    """
    tens = (decimal_val // 10) % 10
    ones = decimal_val % 10
    return (tens << 4) | ones


def lower3(byte_val: int) -> int:
    """Extract lower 3 bits from byte.

    Args:
        byte_val: Input byte

    Returns:
        Lower 3 bits as integer
    """
    return byte_val & LOWER3


def upper5(byte_val: int) -> int:
    """Extract upper 5 bits from byte.

    Args:
        byte_val: Input byte

    Returns:
        Upper 5 bits as integer
    """
    return (byte_val & UPPER5) >> 3


def byte_to_bits(byte_value: int) -> List[bool]:
    """Convert a byte value to 8-bit boolean array.

    Args:
        byte_value: Byte value to convert

    Returns:
        List of 8 boolean values representing the bits
    """
    return [(byte_value & (1 << n)) != 0 for n in range(8)]


def bits_to_byte(bits: List[bool]) -> int:
    """Convert boolean array to byte value.

    Args:
        bits: List of boolean values representing bits

    Returns:
        Byte value
    """
    byte_val = 0
    for i, bit in enumerate(bits[:8]):  # Limit to 8 bits
        if bit:
            byte_val |= 1 << i
    return byte_val


def highest_bit_set(value: int) -> int:
    """Remove the high bit (0x80) from a byte value.

    Args:
        value: Byte value to process

    Returns:
        Value with high bit cleared (XOR with 0x80 if high bit was set)
    """
    return (value & 0x80) == 128


def remove_highest_bit(value: int) -> int:
    """Remove the high bit (0x80) from a byte value.

    Args:
        value: Byte value to process

    Returns:
        Value with high bit cleared (XOR with 0x80 if high bit was set)
    """
    return value ^ 0x80 if (value & 0x80) == 128 else value


def byte_to_unsigned(byte_val: int) -> int:
    """Convert signed byte to unsigned integer.

    Args:
        byte_val: Byte value (can be negative)

    Returns:
        Unsigned integer (0-255)
    """
    if byte_val < 0:
        return byte_val + 256
    return byte_val


def nibble(byte_val: int) -> str:
    """Convert byte value to two-character nibble representation.

    Args:
        byte_val: Byte value (0-255)

    Returns:
        Two-character string representing the nibble
    """
    low_cc = ((byte_val & 0xF0) >> 4) + 65
    high_cc = (byte_val & 0xF) + 65
    return chr(low_cc) + chr(high_cc)


def de_nibble(nibble_str: str) -> int:
    """Convert two-character nibble string to byte value.

    Based on pseudocode: A=0, B=1, C=2, ..., P=15

    Args:
        nibble_str: Two-character string with A-P encoding

    Returns:
        Byte value (0-255)

    Raises:
        ValueError: If nibble string is not exactly 2 characters
    """
    if len(nibble_str) != 2:
        raise ValueError("Nibble string must be exactly 2 characters")

    high_char = nibble_str[0]
    low_char = nibble_str[1]

    # Convert A-P to 0-15 (A=65 in ASCII, so A-65=0)
    high_nibble = (ord(high_char) - 65) << 4
    low_nibble = ord(low_char) - 65

    return high_nibble + low_nibble


def de_nibbles(str_val: str) -> bytearray:
    """Convert hex string with A-P encoding to list of integers.

    Based on pseudocode: A=0, B=1, C=2, ..., P=15

    Args:
        str_val: Hex string with A-P encoding

    Returns:
        List of integers representing the decoded bytes

    Raises:
        ValueError: If string length is not even for nibble conversion
    """
    if len(str_val) % 2 != 0:
        raise ValueError("String length must be even for nibble conversion")

    result = bytearray()
    for i in range(0, len(str_val), 2):
        result.append(de_nibble(str_val[i : i + 2]))
    return result


def nibbles(data: bytes) -> str:
    """Convert bytes data to nibble string representation.

    Args:
        data: Bytes data to convert

    Returns:
        String representation using A-P encoding
    """
    return "".join(nibble(byte) for byte in data)

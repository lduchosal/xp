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


def a_byte_to_int_no_sign(byte_val: int) -> int:
    """Convert signed byte to unsigned integer.

    Args:
        byte_val: Byte value (can be negative)

    Returns:
        Unsigned integer (0-255)
    """
    if byte_val < 0:
        return byte_val + 256
    return byte_val

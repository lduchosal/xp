"""Checksum utility functions for protocol interoperability.

This module provides standard checksum calculation functions for protocol
communication compatibility, including XOR checksum and IEEE 802.3 CRC32.
Implemented for interoperability purposes under fair use provisions.

Copyright (c) 2025 ld
Licensed under MIT License - see LICENSE file for details.
"""


def calculate_checksum(buffer: str) -> str:
    """Calculate simple XOR checksum of a string buffer.

    Args:
        buffer: Input string to calculate checksum for

    Returns:
        Two-character checksum string in nibble format
    """
    cc = 0
    for char in buffer:
        cc ^= ord(char)

    return nibble(cc & 0xFF)


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


def de_nibble(str_val: str) -> bytearray:
    """Convert hex string with A-P encoding to list of integers.

    Based on pseudo code: A=0, B=1, C=2, ..., P=15

    Args:
        str_val: Hex string with A-P encoding

    Returns:
        List of integers representing the decoded bytes
    """
    if len(str_val) % 2 != 0:
        raise ValueError("String length must be even for nibble conversion")

    result = bytearray()
    for i in range(0, len(str_val), 2):
        # Get high and low nibbles
        high_char = str_val[i]
        low_char = str_val[i + 1]

        # Convert A-P to 0-15 (A=65 in ASCII, so A-65=0)
        high_nibble = (ord(high_char) - 65) << 4
        low_nibble = ord(low_char) - 65

        result.extend([high_nibble + low_nibble])
    return result


def un_bcd(bcd: int) -> int:
    """Convert BCD (Binary Coded Decimal) to integer.

    Args:
        bcd: BCD value

    Returns:
        Integer representation
    """
    i_bcd = a_byte_to_int_no_sign(bcd)
    return (i_bcd >> 4) * 10 + (i_bcd & 0xF)


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


def calculate_checksum32(buffer: bytes) -> str:
    """Calculate CRC32 checksum for protocol interoperability.

    Implements standard CRC32 algorithm using IEEE 802.3 polynomial 0xEDB88320
    for interoperability with XP protocol communications. This is a standard
    algorithm implementation for protocol compatibility purposes.

    Args:
        buffer: Byte array to calculate checksum for

    Returns:
        Eight-character checksum string in nibble format
    """
    nibble_result = ""
    crc = 0xFFFFFFFF  # Initialize to -1 (all bits set)

    for byte in buffer:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320
            else:
                crc = crc >> 1

    crc ^= 0xFFFFFFFF  # Final XOR

    # Convert to nibble format (4 bytes, little-endian)
    for _ in range(4):
        nibble_result = nibble(crc & 0xFF) + nibble_result
        crc >>= 8

    return nibble_result

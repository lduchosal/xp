"""Checksum utility functions for telegram protocol.

This module provides checksum calculation functions equivalent to the Java implementation,
including both simple XOR checksum and CRC32 checksum with custom polynomial.
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

    return _nibble(cc & 0xFF)


def _nibble(byte_val: int) -> str:
    """Convert byte value to two-character nibble representation.

    Args:
        byte_val: Byte value (0-255)

    Returns:
        Two-character string representing the nibble
    """
    low_cc = ((byte_val & 0xF0) >> 4) + 65
    high_cc = (byte_val & 0xF) + 65
    return chr(low_cc) + chr(high_cc)


def de_nibble(str_val: str) -> bytes:
    """Convert nibble string back to bytes.

    Args:
        str_val: Nibble string (even length)

    Returns:
        Byte array representation

    Raises:
        ValueError: If string length is odd
    """
    if len(str_val) % 2 != 0:
        raise ValueError("String length must be even for nibble conversion")

    result = bytearray()
    for i in range(0, len(str_val), 2):
        low_cc = (ord(str_val[i]) - 65) << 4
        high_cc = ord(str_val[i + 1]) - 65
        result.append((low_cc + high_cc) & 0xFF)

    return bytes(result)


def un_bcd(bcd: int) -> int:
    """Convert BCD (Binary Coded Decimal) to integer.

    Args:
        bcd: BCD value

    Returns:
        Integer representation
    """
    i_bcd = _byte_to_int_no_sign(bcd)
    return (i_bcd >> 4) * 10 + (i_bcd & 0xF)


def _byte_to_int_no_sign(byte_val: int) -> int:
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
    """Calculate CRC32 checksum with custom polynomial.

    This implements the same CRC32 algorithm as the Java version,
    using polynomial 0xEDB88320.

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
        nibble_result = _nibble(crc & 0xFF) + nibble_result
        crc >>= 8

    return nibble_result

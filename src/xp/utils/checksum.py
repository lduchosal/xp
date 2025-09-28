"""Checksum utility functions for protocol interoperability.

This module provides standard checksum calculation functions for protocol
communication compatibility, including XOR checksum and IEEE 802.3 CRC32.
Implemented for interoperability purposes under fair use provisions.

Copyright (c) 2025 ld
Licensed under MIT License - see LICENSE file for details.
"""

from xp.utils.serialization import nibble


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

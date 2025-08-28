"""Discover telegram models for console bus communication.

Discovery telegrams are used for device enumeration on the console bus.
The master sends a broadcast discovery request, and all devices respond with their serial numbers.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class DiscoveryFunction(Enum):
    """Discovery function codes"""
    DISCOVERY_REQUEST = "01"  # F01D00 - Discovery broadcast request
    DISCOVERY_RESPONSE = "01"  # F01D + checksum suffix - Discovery response
    
    @classmethod
    def from_code(cls, code: str) -> Optional['DiscoveryFunction']:
        """Get DiscoveryFunction from code string"""
        for func in cls:
            if func.value == code:
                return func
        return None


@dataclass
class DiscoveryRequest:
    """
    Represents a discovery request telegram (broadcast from master).
    
    Format: <S0000000000F01D00FA>
    
    Fields:
    - S: Send/System command indicator
    - 0000000000: Source address (all zeros for broadcast)
    - F01D00: Discovery command
    - FA: Checksum
    """
    source_address: str  # Should be "0000000000" for broadcast
    command: str        # Should be "F01D00" for discovery
    checksum: str
    raw_telegram: str
    timestamp: Optional[datetime] = None
    checksum_validated: Optional[bool] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def is_broadcast(self) -> bool:
        """Check if this is a broadcast request (source address all zeros)"""
        return self.source_address == "0000000000"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "source_address": self.source_address,
            "command": self.command,
            "checksum": self.checksum,
            "checksum_validated": self.checksum_validated,
            "is_broadcast": self.is_broadcast,
            "raw_telegram": self.raw_telegram,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "telegram_type": "discovery_request"
        }
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        broadcast_info = "Broadcast " if self.is_broadcast else f"From {self.source_address} "
        return f"Discovery Request: {broadcast_info}Command"


@dataclass
class DiscoveryResponse:
    """
    Represents a discovery response telegram from a device.
    
    Format: <R{10-digit-serial}F01D{checksum}>
    Example: <R0020030837F01DFM>
    
    Fields:
    - R: Response indicator
    - serial_number: 10-digit unique device serial number
    - F01D: Discovery response command base
    - checksum: Single character checksum
    """
    serial_number: str
    command_base: str   # Should be "F01D" for discovery responses
    checksum: str
    raw_telegram: str
    timestamp: Optional[datetime] = None
    checksum_validated: Optional[bool] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def device_id(self) -> str:
        """Get the device identifier (serial number)"""
        return self.serial_number
    
    @property
    def full_command(self) -> str:
        """Get the full command including checksum suffix"""
        return f"{self.command_base}{self.checksum}"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "serial_number": self.serial_number,
            "device_id": self.device_id,
            "command_base": self.command_base,
            "full_command": self.full_command,
            "checksum": self.checksum,
            "checksum_validated": self.checksum_validated,
            "raw_telegram": self.raw_telegram,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "telegram_type": "discovery_response"
        }
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        return f"Discovery Response: Device {self.serial_number} Online"


@dataclass
class DiscoveryResult:
    """
    Represents the result of a discovery operation.
    
    Contains the original request and all received responses.
    """
    request: DiscoveryRequest
    responses: list[DiscoveryResponse]
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def device_count(self) -> int:
        """Number of devices discovered"""
        return len(self.responses)
    
    @property
    def device_serial_numbers(self) -> list[str]:
        """List of all discovered device serial numbers"""
        return [response.serial_number for response in self.responses]
    
    @property
    def has_duplicate_devices(self) -> bool:
        """Check if there are duplicate serial numbers (indicates error)"""
        serials = self.device_serial_numbers
        return len(serials) != len(set(serials))
    
    @property
    def duplicate_devices(self) -> list[str]:
        """Get list of duplicate serial numbers"""
        serials = self.device_serial_numbers
        seen = set()
        duplicates = []
        for serial in serials:
            if serial in seen and serial not in duplicates:
                duplicates.append(serial)
            seen.add(serial)
        return duplicates
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "request": self.request.to_dict(),
            "responses": [response.to_dict() for response in self.responses],
            "device_count": self.device_count,
            "device_serial_numbers": self.device_serial_numbers,
            "has_duplicate_devices": self.has_duplicate_devices,
            "duplicate_devices": self.duplicate_devices,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "result_type": "discovery_result"
        }
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        if self.device_count == 0:
            return "Discovery Result: No devices found"
        elif self.device_count == 1:
            return f"Discovery Result: 1 device found ({self.device_serial_numbers[0]})"
        else:
            return f"Discovery Result: {self.device_count} devices found"
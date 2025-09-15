"""Conbus Client Send data models"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class TelegramType(Enum):
    """Supported telegram types for Conbus client send operations"""
    DISCOVERY = "discovery"
    VERSION = "version"
    VOLTAGE = "voltage"
    TEMPERATURE = "temperature"
    CURRENT = "current"
    HUMIDITY = "humidity"
    BLINK = "blink"
    UNBLINK = "unblink"


@dataclass
class ConbusClientConfig:
    """Configuration for Conbus client connection"""
    ip: str = "192.168.1.100"
    port: int = 10001
    timeout: int = 10
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "ip": self.ip,
            "port": self.port,
            "timeout": self.timeout
        }


@dataclass
class ConbusSendRequest:
    """Represents a Conbus send request"""
    telegram_type: TelegramType
    target_serial: Optional[str] = None
    function_code: Optional[str] = None
    data_point_code: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "telegram_type": self.telegram_type.value,
            "target_serial": self.target_serial,
            "function_code": self.function_code,
            "data_point_code": self.data_point_code,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


@dataclass
class ConbusSendResponse:
    """Represents a response from Conbus send operation"""
    success: bool
    request: ConbusSendRequest
    sent_telegram: Optional[str] = None
    received_telegrams: Optional[list] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.received_telegrams is None:
            self.received_telegrams = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "success": self.success,
            "request": self.request.to_dict(),
            "sent_telegram": self.sent_telegram,
            "received_telegrams": self.received_telegrams,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


@dataclass
class ConbusConnectionStatus:
    """Represents the current connection status"""
    connected: bool
    ip: str
    port: int
    last_activity: Optional[datetime] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "connected": self.connected,
            "ip": self.ip,
            "port": self.port,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "error": self.error
        }
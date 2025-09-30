from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ConbusClientConfig:
    """Configuration for Conbus client connection"""

    ip: str = "192.168.1.100"
    port: int = 10001
    timeout: float = 0.1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {"ip": self.ip, "port": self.port, "timeout": self.timeout}

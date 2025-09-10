"""Base Server Service with shared functionality.

This module provides a base class for all XP device server services,
containing common functionality like module type response generation.
"""

import logging
from typing import Optional
from abc import ABC

from ..models.system_telegram import SystemTelegram, SystemFunction, DataPointType
from ..utils.checksum import calculate_checksum


class BaseServerService(ABC):
    """
    Base class for all XP device server services.
    
    Provides common functionality that is shared across all device types,
    such as module type response generation.
    """
    
    def __init__(self, serial_number: str):
        """Initialize base server service"""
        self.serial_number = serial_number
        self.logger = logging.getLogger(__name__)
        
        # Must be set by subclasses
        self.device_type = None
        self.module_type_code = None
    
    def generate_module_type_response(self, request: SystemTelegram) -> Optional[str]:
        """Generate module type response telegram"""
        if (request.system_function == SystemFunction.RETURN_DATA and
            request.data_point_id == DataPointType.MODULE_TYPE):
            
            if self.module_type_code is None:
                self.logger.error(f"Module type code not set for {self.device_type}")
                return None
            
            # Format module type code as hex if it's an integer
            if isinstance(self.module_type_code, int):
                module_type_hex = f"{self.module_type_code:02X}"
            else:
                module_type_hex = str(self.module_type_code)
            
            data_part = f"R{self.serial_number}F02D07{module_type_hex}"
            checksum = calculate_checksum(data_part)
            telegram = f"<{data_part}{checksum}>"
            
            self.logger.debug(f"Generated {self.device_type} module type response: {telegram}")
            return telegram
        
        return None
    
    def _check_request_for_device(self, request: SystemTelegram) -> bool:
        """Check if request is for this device (including broadcast)"""
        return (request.serial_number == self.serial_number or 
                request.serial_number == "0000000000")
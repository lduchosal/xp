"""XP230 Server Service for device emulation.

This service provides XP230-specific device emulation functionality,
including response generation and device configuration handling.
"""

import logging
from typing import Dict, Optional
from ..models.system_telegram import SystemTelegram, SystemFunction, DataPointType
from ..models.reply_telegram import ReplyTelegram
from ..utils.checksum import calculate_checksum


class XP230ServerError(Exception):
    """Raised when XP230 server operations fail"""
    pass


class XP230ServerService:
    """
    XP230 device emulation service.
    
    Generates XP230-specific responses, handles XP230 device configuration,
    and implements XP230 telegram format.
    """
    
    def __init__(self, serial_number: str):
        """Initialize XP230 server service"""
        self.serial_number = serial_number
        self.device_type = "XP230"
        self.logger = logging.getLogger(__name__)
        
        # XP230 device characteristics
        self.firmware_version = "XP230_V1.00.04"
        self.device_status = "OK"
        self.link_number = 1
        self.module_type_code = 24  # XP230 module type from registry
    
    def generate_discovery_response(self) -> str:
        """Generate XP230 discovery response telegram"""
        # Format: <R{serial}F01D{checksum}>
        data_part = f"R{self.serial_number}F01D"
        checksum = calculate_checksum(data_part)
        telegram = f"<{data_part}{checksum}>"
        
        self.logger.debug(f"Generated XP230 discovery response: {telegram}")
        return telegram
    
    def generate_version_response(self, request: SystemTelegram) -> Optional[str]:
        """Generate version response telegram"""
        if (request.system_function == SystemFunction.RETURN_DATA and
            request.data_point_id == DataPointType.VERSION):
            
            # Format: <R{serial}F02D02{version}{checksum}>
            data_part = f"R{self.serial_number}F02D02{self.firmware_version}"
            checksum = calculate_checksum(data_part)
            telegram = f"<{data_part}{checksum}>"
            
            self.logger.debug(f"Generated XP230 version response: {telegram}")
            return telegram
        
        return None
    
    def generate_status_response(self, request: SystemTelegram) -> Optional[str]:
        """Generate status response telegram"""
        if (request.system_function == SystemFunction.RETURN_DATA and
            request.data_point_id == DataPointType.STATUS):
            
            # Format: <R{serial}F02D00{status}{checksum}>
            data_part = f"R{self.serial_number}F02D00{self.device_status}"
            checksum = calculate_checksum(data_part)
            telegram = f"<{data_part}{checksum}>"
            
            self.logger.debug(f"Generated XP230 status response: {telegram}")
            return telegram
        
        return None
    
    def generate_link_number_response(self, request: SystemTelegram) -> Optional[str]:
        """Generate link number response telegram"""
        if (request.system_function == SystemFunction.RETURN_DATA and
            request.data_point_id == DataPointType.LINK_NUMBER):
            
            # Format: <R{serial}F02D04{link_number}{checksum}>
            # Link number is typically encoded as 2-digit hex
            link_hex = f"{self.link_number:02X}"
            data_part = f"R{self.serial_number}F02D04{link_hex}"
            checksum = calculate_checksum(data_part)
            telegram = f"<{data_part}{checksum}>"
            
            self.logger.debug(f"Generated XP230 link number response: {telegram}")
            return telegram
        
        return None
    
    def set_link_number(self, request: SystemTelegram, new_link_number: int) -> Optional[str]:
        """Set link number and generate ACK response"""
        if (request.system_function == SystemFunction.WRITE_CONFIG and
            request.data_point_id == DataPointType.LINK_NUMBER):
            
            # Update internal link number
            self.link_number = new_link_number
            
            # Generate ACK response: <R{serial}F18D{checksum}>
            data_part = f"R{self.serial_number}F18D"
            checksum = calculate_checksum(data_part)
            telegram = f"<{data_part}{checksum}>"
            
            self.logger.info(f"XP230 link number set to {new_link_number}")
            return telegram
        
        return None
    
    def generate_module_type_response(self, request: SystemTelegram) -> Optional[str]:
        """Generate module type response telegram"""
        if (request.system_function == SystemFunction.RETURN_DATA and
            request.data_point_id == DataPointType.MODULE_TYPE):
            
            # XP230 code is 24, return as 2-digit hex  
            module_type_hex = f"{self.module_type_code:02X}"
            data_part = f"R{self.serial_number}F02D07{module_type_hex}"
            checksum = calculate_checksum(data_part)
            telegram = f"<{data_part}{checksum}>"
            
            self.logger.debug(f"Generated XP230 module type response: {telegram}")
            return telegram
        
        return None
    
    def generate_temperature_response(self, request: SystemTelegram) -> Optional[str]:
        """Generate temperature response telegram (simulated)"""
        if (request.system_function == SystemFunction.RETURN_DATA and
            request.data_point_id == DataPointType.TEMPERATURE):
            
            # Simulate temperature reading: +50.5°C (from ConReport.log)
            temperature_value = "+50,5§C"
            data_part = f"R{self.serial_number}F02D18{temperature_value}"
            checksum = calculate_checksum(data_part)
            telegram = f"<{data_part}{checksum}>"
            
            self.logger.debug(f"Generated XP230 temperature response: {telegram}")
            return telegram
        
        return None
    
    def process_system_telegram(self, request: SystemTelegram) -> Optional[str]:
        """Process system telegram and generate appropriate response"""
        # Check if request is for this device
        if request.serial_number != self.serial_number and request.serial_number != "0000000000":
            return None
        
        # Handle different system functions
        if request.system_function == SystemFunction.DISCOVERY:
            return self.generate_discovery_response()
        
        elif request.system_function == SystemFunction.RETURN_DATA:
            # Handle different data point requests
            if request.data_point_id == DataPointType.VERSION:
                return self.generate_version_response(request)
            elif request.data_point_id == DataPointType.STATUS:
                return self.generate_status_response(request)
            elif request.data_point_id == DataPointType.LINK_NUMBER:
                return self.generate_link_number_response(request)
            elif request.data_point_id == DataPointType.MODULE_TYPE:
                return self.generate_module_type_response(request)
            elif request.data_point_id == DataPointType.TEMPERATURE:
                return self.generate_temperature_response(request)
        
        elif request.system_function == SystemFunction.WRITE_CONFIG:
            if request.data_point_id == DataPointType.LINK_NUMBER:
                # Extract link number from request data
                # This would need more sophisticated parsing in real implementation
                return self.set_link_number(request, 1)
        
        self.logger.warning(f"Unhandled XP230 request: {request}")
        return None
    
    def get_device_info(self) -> Dict:
        """Get XP230 device information"""
        return {
            "serial_number": self.serial_number,
            "device_type": self.device_type,
            "firmware_version": self.firmware_version,
            "status": self.device_status,
            "link_number": self.link_number
        }
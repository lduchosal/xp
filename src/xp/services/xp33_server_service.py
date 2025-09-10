"""XP33 Server Service for device emulation.

This service provides XP33-specific device emulation functionality,
including response generation and device configuration handling for
3-channel light dimmer modules.
"""

import logging
from typing import Dict, Optional, List
from ..models.system_telegram import SystemTelegram, SystemFunction, DataPointType
from ..models.reply_telegram import ReplyTelegram
from ..utils.checksum import calculate_checksum


class XP33ServerError(Exception):
    """Raised when XP33 server operations fail"""
    pass


class XP33ServerService:
    """
    XP33 device emulation service.
    
    Generates XP33-specific responses, handles XP33 device configuration,
    and implements XP33 telegram format for 3-channel dimmer modules.
    """
    
    def __init__(self, serial_number: str, variant: str = "XP33LR"):
        """Initialize XP33 server service"""
        self.serial_number = serial_number
        self.variant = variant  # XP33LR or XP33LED
        self.device_type = "XP33"
        self.logger = logging.getLogger(__name__)
        
        # XP33 device characteristics
        if variant == "XP33LED":
            self.firmware_version = "XP33LED_V0.04.02"
            self.ean_code = "5703513058999"
            self.max_power = 300  # 3 x 100VA
        else:  # XP33LR
            self.firmware_version = "XP33LR_V0.04.02"
            self.ean_code = "5703513058982"
            self.max_power = 640  # Total 640VA
        
        self.device_status = "00"  # Normal status
        self.link_count = 4  # 4 links configured
        self.module_type_code = 11  # XP33 module type
        
        # Channel states (3 channels, 0-100% dimming)
        self.channel_states = [0, 0, 0]  # All channels at 0%
        
        # Scene configuration (4 scenes)
        self.scenes = {
            1: [50, 30, 20],  # Scene 1: 50%, 30%, 20%
            2: [100, 100, 100],  # Scene 2: All full
            3: [25, 25, 25],  # Scene 3: Low level
            4: [0, 0, 0]  # Scene 4: Off
        }
    
    def generate_discovery_response(self) -> str:
        """Generate XP33 discovery response telegram"""
        # Format: <R{serial}F01D{checksum}>
        data_part = f"R{self.serial_number}F01D"
        checksum = calculate_checksum(data_part)
        telegram = f"<{data_part}{checksum}>"
        
        self.logger.debug(f"Generated XP33 discovery response: {telegram}")
        return telegram
    
    def generate_version_response(self, request: SystemTelegram) -> Optional[str]:
        """Generate version response telegram"""
        if (request.system_function == SystemFunction.RETURN_DATA and
            request.data_point_id == DataPointType.VERSION):
            
            # Format: <R{serial}F02D02{version}{checksum}>
            data_part = f"R{self.serial_number}F02D02{self.firmware_version}"
            checksum = calculate_checksum(data_part)
            telegram = f"<{data_part}{checksum}>"
            
            self.logger.debug(f"Generated XP33 version response: {telegram}")
            return telegram
        
        return None
    
    def generate_module_type_response(self, request: SystemTelegram) -> Optional[str]:
        """Generate module type response telegram"""
        if (request.system_function == SystemFunction.RETURN_DATA and
            request.data_point_id == DataPointType.MODULE_TYPE):
            
            # XP33 code is 11, with offset becomes 48 decimal = 30 hex
            module_type_hex = f"{self.module_type_code + 37:02X}"  # 11 + 37 = 48 = 0x30
            data_part = f"R{self.serial_number}F02D07{module_type_hex}"
            checksum = calculate_checksum(data_part)
            telegram = f"<{data_part}{checksum}>"
            
            self.logger.debug(f"Generated XP33 module type response: {telegram}")
            return telegram
        
        return None
    
    def generate_status_response(self, request: SystemTelegram) -> Optional[str]:
        """Generate status response telegram"""
        if (request.system_function == SystemFunction.RETURN_DATA and
            request.data_point_id == DataPointType.STATUS_QUERY):
            
            # Format: <R{serial}F02D10{status}{checksum}>
            data_part = f"R{self.serial_number}F02D10{self.device_status}"
            checksum = calculate_checksum(data_part)
            telegram = f"<{data_part}{checksum}>"
            
            self.logger.debug(f"Generated XP33 status response: {telegram}")
            return telegram
        
        return None
    
    def generate_channel_states_response(self, request: SystemTelegram) -> Optional[str]:
        """Generate channel states response telegram"""
        if (request.system_function == SystemFunction.RETURN_DATA and
            request.data_point_id == DataPointType.CHANNEL_STATES):
            
            # Format: xxxxx000 (3 channels + padding)
            # Each channel: 00-64 hex (0-100%)
            ch1_hex = f"{int(self.channel_states[0] * 100 / 100):02X}"
            ch2_hex = f"{int(self.channel_states[1] * 100 / 100):02X}"
            ch3_hex = f"{int(self.channel_states[2] * 100 / 100):02X}"
            
            channel_data = f"{ch1_hex}{ch2_hex}{ch3_hex}000"
            data_part = f"R{self.serial_number}F02D12{channel_data}"
            checksum = calculate_checksum(data_part)
            telegram = f"<{data_part}{checksum}>"
            
            self.logger.debug(f"Generated XP33 channel states response: {telegram}")
            return telegram
        
        return None
    
    def generate_link_count_response(self, request: SystemTelegram) -> Optional[str]:
        """Generate link count response telegram"""
        if (request.system_function == SystemFunction.RETURN_DATA and
            request.data_point_id in [DataPointType.LINK_COUNT, DataPointType.LINK_NUMBER]):
            
            # Format: <R{serial}F02D04{count}{checksum}>
            link_hex = f"{self.link_count:02X}"
            data_part = f"R{self.serial_number}F02D04{link_hex}"
            checksum = calculate_checksum(data_part)
            telegram = f"<{data_part}{checksum}>"
            
            self.logger.debug(f"Generated XP33 link count response: {telegram}")
            return telegram
        
        return None
    
    def set_channel_dimming(self, channel: int, level: int) -> bool:
        """Set individual channel dimming level"""
        if 1 <= channel <= 3 and 0 <= level <= 100:
            self.channel_states[channel - 1] = level
            self.logger.info(f"XP33 channel {channel} set to {level}%")
            return True
        return False
    
    def activate_scene(self, scene: int) -> bool:
        """Activate a pre-programmed scene"""
        if scene in self.scenes:
            self.channel_states = self.scenes[scene].copy()
            self.logger.info(f"XP33 scene {scene} activated: {self.channel_states}")
            return True
        return False
    
    def generate_channel_control_response(self, request: SystemTelegram) -> Optional[str]:
        """Generate individual channel control response"""
        # Check for individual channel data points
        channel_mapping = {
            DataPointType.CHANNEL_1: 1,
            DataPointType.CHANNEL_2: 2,
            DataPointType.CHANNEL_3: 3
        }
        
        if (request.system_function == SystemFunction.RETURN_DATA and
            request.data_point_id in channel_mapping):
            
            channel = channel_mapping[request.data_point_id]
            
            # Return current channel state in 5-hex format
            ch1_hex = f"{int(self.channel_states[0] * 100 / 100):02X}"
            ch2_hex = f"{int(self.channel_states[1] * 100 / 100):02X}"
            ch3_hex = f"{int(self.channel_states[2] * 100 / 100):02X}"
            
            channel_data = f"{ch1_hex}{ch2_hex}{ch3_hex}00"
            data_part = f"R{self.serial_number}F02D{request.data_point_id.value}{channel_data}"
            checksum = calculate_checksum(data_part)
            telegram = f"<{data_part}{checksum}>"
            
            self.logger.debug(f"Generated XP33 channel {channel} response: {telegram}")
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
            elif request.data_point_id == DataPointType.MODULE_TYPE:
                return self.generate_module_type_response(request)
            elif request.data_point_id == DataPointType.STATUS_QUERY:
                return self.generate_status_response(request)
            elif request.data_point_id == DataPointType.CHANNEL_STATES:
                return self.generate_channel_states_response(request)
            elif request.data_point_id in [DataPointType.LINK_COUNT, DataPointType.LINK_NUMBER]:
                return self.generate_link_count_response(request)
            elif request.data_point_id in [DataPointType.CHANNEL_1, DataPointType.CHANNEL_2, DataPointType.CHANNEL_3]:
                return self.generate_channel_control_response(request)
        
        self.logger.warning(f"Unhandled XP33 request: {request}")
        return None
    
    def get_device_info(self) -> Dict:
        """Get XP33 device information"""
        return {
            "serial_number": self.serial_number,
            "device_type": self.device_type,
            "variant": self.variant,
            "firmware_version": self.firmware_version,
            "ean_code": self.ean_code,
            "max_power": self.max_power,
            "status": self.device_status,
            "link_count": self.link_count,
            "channel_states": self.channel_states.copy(),
            "available_scenes": list(self.scenes.keys())
        }
    
    def get_technical_specs(self) -> Dict:
        """Get technical specifications"""
        if self.variant == "XP33LED":
            return {
                "power_per_channel": "100VA",
                "total_power": "300VA",
                "load_types": ["LED lamps", "resistive", "capacitive"],
                "dimming_type": "Leading/Trailing edge configurable",
                "protection": "Short-circuit proof channels"
            }
        else:  # XP33LR
            return {
                "power_per_channel": "500VA max",
                "total_power": "640VA",
                "load_types": ["Resistive", "inductive"],
                "dimming_type": "Leading edge, logarithmic control",
                "protection": "Thermal protection, neutral break detection"
            }
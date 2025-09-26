"""XP33 Server Service for device emulation.

This service provides XP33-specific device emulation functionality,
including response generation and device configuration handling for
3-channel light dimmer modules.
"""

from typing import Dict, Optional
from ..models.system_telegram import SystemTelegram
from ..models.datapoint_type import DataPointType
from ..models.system_function import SystemFunction
from .base_server_service import BaseServerService


class XP33ServerError(Exception):
    """Raised when XP33 server operations fail"""

    pass


class XP33ServerService(BaseServerService):
    """
    XP33 device emulation service.

    Generates XP33-specific responses, handles XP33 device configuration,
    and implements XP33 telegram format for 3-channel dimmer modules.
    """

    def __init__(self, serial_number: str, variant: str = "XP33LR"):
        """Initialize XP33 server service"""
        super().__init__(serial_number)
        self.variant = variant  # XP33 or XP33LR or XP33LED
        self.device_type = "XP33"
        self.module_type_code = 11  # XP33 module type

        # XP33 device characteristics (anonymized for interoperability testing)
        if variant == "XP33LED":
            self.firmware_version = "XP33LED_V0.00.00"
            self.ean_code = "1234567890123"  # Test EAN - not a real product code
            self.max_power = 300  # 3 x 100VA
            self.module_type_code = 31  # XP33LR module type
        elif variant == "XP33LR":  # XP33LR
            self.firmware_version = "XP33LR_V0.00.00"
            self.ean_code = "1234567890124"  # Test EAN - not a real product code
            self.max_power = 640  # Total 640VA
            self.module_type_code = 30  # XP33LR module type
        else:  # XP33
            self.firmware_version = "XP33_V0.04.02"
            self.ean_code = "1234567890125"  # Test EAN - not a real product code
            self.max_power = 100  # Total 640VA
            self.module_type_code = 11  # XP33 module type

        self.device_status = "00"  # Normal status
        self.link_number = 4  # 4 links configured

        # Channel states (3 channels, 0-100% dimming)
        self.channel_states = [0, 0, 0]  # All channels at 0%

        # Scene configuration (4 scenes)
        self.scenes = {
            1: [50, 30, 20],  # Scene 1: 50%, 30%, 20%
            2: [100, 100, 100],  # Scene 2: All full
            3: [25, 25, 25],  # Scene 3: Low level
            4: [0, 0, 0],  # Scene 4: Off
        }

    def generate_channel_states_response(
        self, request: SystemTelegram
    ) -> Optional[str]:
        """Generate channel states response telegram"""
        if (
            request.system_function == SystemFunction.READ_DATAPOINT
            and request.datapoint_type == DataPointType.MODULE_OUTPUT_STATE
        ):
            # Format: xxxxx000 (3 channels + padding)
            # Each channel: 00-64 hex (0-100%)
            ch1_hex = f"{int(self.channel_states[0] * 100 / 100):02X}"
            ch2_hex = f"{int(self.channel_states[1] * 100 / 100):02X}"
            ch3_hex = f"{int(self.channel_states[2] * 100 / 100):02X}"

            channel_data = f"{ch1_hex}{ch2_hex}{ch3_hex}000"
            data_part = f"R{self.serial_number}F02D12{channel_data}"
            telegram = self._build_response_telegram(data_part)
            self._log_response("channel states", telegram)
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

    def generate_status_response(
        self,
        request: SystemTelegram,
        status_data_point: DataPointType = DataPointType.MODULE_ERROR_CODE,
    ) -> Optional[str]:
        """Generate status response telegram for XP33 (uses STATUS_QUERY)"""
        if (
            request.system_function == SystemFunction.READ_DATAPOINT
            and request.datapoint_type == status_data_point
        ):
            # Format: <R{serial}F02D10{status}{checksum}>
            data_part = f"R{self.serial_number}F02D10{self.device_status}"
            telegram = self._build_response_telegram(data_part)
            self._log_response("status", telegram)
            return telegram

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
            "link_number": self.link_number,
            "channel_states": self.channel_states.copy(),
            "available_scenes": list(self.scenes.keys()),
        }

    def get_technical_specs(self) -> Dict:
        """Get technical specifications"""
        if self.variant == "XP33LED":
            return {
                "power_per_channel": "100VA",
                "total_power": "300VA",
                "load_types": ["LED lamps", "resistive", "capacitive"],
                "dimming_type": "Leading/Trailing edge configurable",
                "protection": "Short-circuit proof channels",
            }

        # XP33LR
        return {
            "power_per_channel": "500VA max",
            "total_power": "640VA",
            "load_types": ["Resistive", "inductive"],
            "dimming_type": "Leading edge, logarithmic control",
            "protection": "Thermal protection, neutral break detection",
        }

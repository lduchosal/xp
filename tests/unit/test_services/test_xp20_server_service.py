from xp.services.xp20_server_service import XP20ServerService
from xp.models.system_telegram import SystemTelegram
from xp.models.datapoint_type import DataPointType
from xp.models.system_function import SystemFunction
from xp.services.telegram_service import TelegramService


class TestXP20ServerService:
    """Test cases for XP20ServerService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.xp20_service = XP20ServerService("0012345002")
        self.telegram_service = TelegramService()

    def test_init(self):
        """Test XP20ServerService initialization"""
        service = XP20ServerService("0012345002")

        assert service.serial_number == "0012345002"
        assert service.device_type == "XP20"
        assert service.firmware_version == "XP20_V0.01.05"
        assert service.device_status == "OK"
        assert service.link_number == 1
        assert service.module_type_code == 33  # XP20 code

    def test_generate_discover_response(self):
        """Test discover response generation"""
        response = self.xp20_service.generate_discover_response()

        assert response == "<R0012345002F01DFC>"
        assert response.startswith("<R0012345002F01D")
        assert response.endswith(">")

    def test_generate_module_type_response(self):
        """Test module type response generation"""
        request = SystemTelegram(
            checksum="FJ",
            raw_telegram="<S0012345002F02D07FJ>",
            serial_number="0012345002",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_TYPE_CODE,
        )

        response = self.xp20_service.generate_module_type_response(request)

        # XP20 should map to hex 33 according to spec
        expected_response = "<R0012345002F02D0733FG>"
        assert response == expected_response
        assert "F02D07" in response
        assert "33" in response  # XP20 code is 33 = 0x21

    def test_generate_module_type_response_wrong_function(self):
        """Test module type response with wrong function returns None"""
        request = SystemTelegram(
            checksum="FJ",
            raw_telegram="<S0012345002F01D07FJ>",
            serial_number="0012345002",
            system_function=SystemFunction.DISCOVERY,  # Wrong function
            datapoint_type=DataPointType.MODULE_TYPE_CODE,
        )

        response = self.xp20_service.generate_module_type_response(request)
        assert response is None

    def test_process_system_telegram_module_type(self):
        """Test processing module type query through main handler"""
        request = SystemTelegram(
            checksum="FJ",
            raw_telegram="<S0012345002F02D07FJ>",
            serial_number="0012345002",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_TYPE_CODE,
        )

        response = self.xp20_service.process_system_telegram(request)

        expected_response = "<R0012345002F02D0733FG>"
        assert response == expected_response
        assert "F02D07" in response
        assert "33" in response

    def test_process_system_telegram_broadcast(self):
        """Test processing telegram with broadcast serial"""
        request = SystemTelegram(
            checksum="FJ",
            raw_telegram="<S0000000000F02D07FJ>",
            serial_number="0000000000",  # Broadcast
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_TYPE_CODE,
        )

        response = self.xp20_service.process_system_telegram(request)

        expected_response = "<R0012345002F02D0733FG>"
        assert response == expected_response
        assert "F02D07" in response
        assert "33" in response

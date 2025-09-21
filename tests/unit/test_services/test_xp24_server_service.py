from xp.services.xp24_server_service import XP24ServerService
from xp.models.system_telegram import SystemTelegram
from xp.models.datapoint_type import DataPointType
from xp.models.system_function import SystemFunction
from xp.services.telegram_service import TelegramService


class TestXP24ServerService:
    """Test cases for XP24ServerService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.xp24_service = XP24ServerService("0012345004")
        self.telegram_service = TelegramService()

    def test_init(self):
        """Test XP24ServerService initialization"""
        service = XP24ServerService("0012345004")

        assert service.serial_number == "0012345004"
        assert service.device_type == "XP24"
        assert service.firmware_version == "XP24_V0.34.03"
        assert service.device_status == "OK"
        assert service.link_number == 1
        assert service.module_type_code == 7

    def test_generate_discover_response(self):
        """Test discover response generation"""
        response = self.xp24_service.generate_discover_response()

        assert response == "<R0012345004F01DFE>"
        assert response.startswith("<R0012345004F01D")
        assert response.endswith(">")

    def test_generate_module_type_response(self):
        """Test module type response generation"""
        request = SystemTelegram(
            checksum="FH",
            raw_telegram="<S0012345004F02D07FH>",
            serial_number="0012345004",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_TYPE_CODE,
        )

        response = self.xp24_service.generate_module_type_response(request)

        assert response == "<R0012345004F02D077GH>"
        assert "F02D07" in response
        assert "07" in response  # XP24 code is 7 = 0x07

    def test_generate_module_type_response_wrong_function(self):
        """Test module type response with wrong function returns None"""
        request = SystemTelegram(
            checksum="FH",
            raw_telegram="<S0012345004F01D07FH>",
            serial_number="0012345004",
            system_function=SystemFunction.DISCOVERY,  # Wrong function
            datapoint_type=DataPointType.MODULE_TYPE_CODE,
        )

        response = self.xp24_service.generate_module_type_response(request)
        assert response is None

    def test_generate_module_type_response_wrong_datapoint(self):
        """Test module type response with wrong data point returns None"""
        request = SystemTelegram(
            checksum="FH",
            raw_telegram="<S0012345004F02D02FH>",
            serial_number="0012345004",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.SW_VERSION,  # Wrong data point
        )

        response = self.xp24_service.generate_module_type_response(request)
        assert response is None

    def test_process_system_telegram_module_type(self):
        """Test processing module type query through main handler"""
        request = SystemTelegram(
            checksum="FH",
            raw_telegram="<S0012345004F02D07FH>",
            serial_number="0012345004",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_TYPE_CODE,
        )

        response = self.xp24_service.process_system_telegram(request)

        assert response == "<R0012345004F02D077GH>"
        assert "F02D07" in response
        assert "07" in response

    def test_process_system_telegram_different_serial(self):
        """Test processing telegram for different serial returns None"""
        request = SystemTelegram(
            checksum="FH",
            raw_telegram="<S9999999999F02D07FH>",
            serial_number="9999999999",  # Different serial
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_TYPE_CODE,
        )

        response = self.xp24_service.process_system_telegram(request)
        assert response is None

    def test_process_system_telegram_broadcast(self):
        """Test processing telegram with broadcast serial"""
        request = SystemTelegram(
            checksum="FH",
            raw_telegram="<S0000000000F02D07FH>",
            serial_number="0000000000",  # Broadcast
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_TYPE_CODE,
        )

        response = self.xp24_service.process_system_telegram(request)

        assert response == "<R0012345004F02D077GH>"
        assert "F02D07" in response
        assert "07" in response

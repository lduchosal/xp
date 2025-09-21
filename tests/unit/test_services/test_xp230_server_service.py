from xp.services.xp230_server_service import XP230ServerService
from xp.models.system_telegram import SystemTelegram
from xp.models.datapoint_type import DataPointType
from xp.models.system_function import SystemFunction
from xp.services.telegram_service import TelegramService


class TestXP230ServerService:
    """Test cases for XP230ServerService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.service = XP230ServerService("0012345011")
        self.telegram_service = TelegramService()

    def test_init(self):
        """Test XP230ServerService initialization"""
        service = XP230ServerService("0012345011")

        assert service.serial_number == "0012345011"
        assert service.device_type == "XP230"
        assert service.firmware_version == "XP230_V1.00.04"
        assert service.device_status == "OK"
        assert service.link_number == 1
        assert service.module_type_code == 34  # XP230 module type

    def test_generate_discover_response(self):
        """Test discover response generation"""
        response = self.service.generate_discover_response()

        # Should generate <R{serial}F01D{checksum}>
        assert response.startswith("<R0012345011F01D")
        assert response.endswith(">")
        assert len(response) == 19  # <R + 10 digits + F01D + 2 char checksum + >

    def test_generate_version_response(self):
        """Test version response generation"""
        request = SystemTelegram(
            serial_number="0012345011",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.SW_VERSION,
            checksum="FM",
            raw_telegram="<S0012345011F02D02FM>",
        )

        response = self.service.generate_version_response(request)

        assert response is not None
        assert "XP230_V1.00.04" in response
        assert response.startswith("<R0012345011F02D02")
        assert response.endswith(">")

    def test_generate_version_response_wrong_request(self):
        """Test version response with wrong request type"""
        request = SystemTelegram(
            serial_number="0012345011",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_TYPE,
            checksum="FM",
            raw_telegram="<S0012345011F02D00FM>",
        )

        response = self.service.generate_version_response(request)
        assert response is None

    def test_generate_status_response(self):
        """Test status response generation"""
        request = SystemTelegram(
            serial_number="0012345011",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_TYPE,
            checksum="FM",
            raw_telegram="<S0012345011F02D00FM>",
        )

        response = self.service.generate_status_response(request)

        assert response is not None
        assert "OK" in response
        assert response.startswith("<R0012345011F02D00")
        assert response.endswith(">")

    def test_generate_link_number_response(self):
        """Test link number response generation"""
        request = SystemTelegram(
            serial_number="0012345011",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.LINK_NUMBER,
            checksum="FO",
            raw_telegram="<S0012345011F02D04FO>",
        )

        response = self.service.generate_link_number_response(request)

        assert response is not None
        assert response.startswith("<R0012345011F02D04")
        assert response.endswith(">")
        # Should contain hex representation of link number (01)
        assert "01" in response

    def test_generate_temperature_response(self):
        """Test temperature response generation"""
        request = SystemTelegram(
            serial_number="0012345011",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0012345011F02D18FN>",
        )

        response = self.service.generate_temperature_response(request)

        assert response is not None
        assert "+50,5§C" in response  # Temperature from ConReport.log
        assert response.startswith("<R0012345011F02D18")
        assert response.endswith(">")

    def test_generate_module_type_response(self):
        """Test module type response generation"""
        request = SystemTelegram(
            serial_number="0012345011",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_TYPE_CODE,
            checksum="FJ",
            raw_telegram="<S0012345011F02D07FJ>",
        )

        response = self.service.generate_module_type_response(request)

        assert response is not None
        assert response == "<R0012345011F02D0734FD>"
        assert "F02D07" in response
        assert "34" in response  # XP230 code is 34

    def test_generate_module_type_response_wrong_function(self):
        """Test module type response with wrong function returns None"""
        request = SystemTelegram(
            serial_number="0012345011",
            system_function=SystemFunction.DISCOVERY,  # Wrong function
            datapoint_type=DataPointType.MODULE_TYPE_CODE,
            checksum="FJ",
            raw_telegram="<S0012345011F01D07FJ>",
        )

        response = self.service.generate_module_type_response(request)
        assert response is None

    def test_process_system_telegram_module_type(self):
        """Test processing module type query through main handler"""
        request = SystemTelegram(
            serial_number="0012345011",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_TYPE_CODE,
            checksum="FJ",
            raw_telegram="<S0012345011F02D07FJ>",
        )

        response = self.service.process_system_telegram(request)

        assert response is not None
        assert response == "<R0012345011F02D0734FD>"
        assert "F02D07" in response
        assert "34" in response  # XP230 code is 34

    def test_set_link_number(self):
        """Test setting link number"""
        request = SystemTelegram(
            serial_number="0012345011",
            system_function=SystemFunction.WRITE_CONFIG,
            datapoint_type=DataPointType.LINK_NUMBER,
            checksum="FO",
            raw_telegram="<S0012345011F04D04FO>",
        )

        response = self.service.set_link_number(request, 3)

        assert response is not None
        assert self.service.link_number == 3
        assert response.startswith("<R0012345011F18D")
        assert response.endswith(">")

    def test_process_system_telegram_discover(self):
        """Test processing discover request"""
        request = SystemTelegram(
            serial_number="0012345011",
            system_function=SystemFunction.DISCOVERY,
            checksum="FG",
            raw_telegram="<S0012345011F01DFG>",
        )

        response = self.service.process_system_telegram(request)

        assert response is not None
        assert response.startswith("<R0012345011F01D")
        assert response.endswith(">")

    def test_process_system_telegram_wrong_serial(self):
        """Test processing request for wrong serial number"""
        request = SystemTelegram(
            serial_number="9999999999",
            system_function=SystemFunction.DISCOVERY,
            checksum="FG",
            raw_telegram="<S9999999999F01DFG>",
        )

        response = self.service.process_system_telegram(request)
        assert response is None

    def test_process_system_telegram_broadcast(self):
        """Test processing broadcast request"""
        request = SystemTelegram(
            serial_number="0000000000",
            system_function=SystemFunction.DISCOVERY,
            checksum="FG",
            raw_telegram="<S0000000000F01DFG>",
        )

        response = self.service.process_system_telegram(request)

        assert response is not None
        assert response.startswith("<R0012345011F01D")
        assert response.endswith(">")

    def test_get_device_info(self):
        """Test getting device information"""
        info = self.service.get_device_info()

        expected_info = {
            "serial_number": "0012345011",
            "device_type": "XP230",
            "firmware_version": "XP230_V1.00.04",
            "status": "OK",
            "link_number": 1,
        }

        assert info == expected_info

from xp.services.base_server_service import BaseServerService
from xp.models.system_telegram import SystemTelegram
from xp.models.datapoint_type import DataPointType
from xp.models.system_function import SystemFunction


class MockServerService(BaseServerService):
    """Mock server service for testing BaseServerService"""

    def __init__(self, serial_number: str):
        super().__init__(serial_number)
        self.device_type = "MOCK"
        self.module_type_code = 42


class TestBaseServerService:
    """Test cases for BaseServerService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.service = MockServerService("1234567890")

    def test_init(self):
        """Test BaseServerService initialization"""
        assert self.service.serial_number == "1234567890"
        assert self.service.device_type == "MOCK"
        assert self.service.module_type_code == 42

    def test_generate_module_type_response(self):
        """Test module type response generation"""
        request = SystemTelegram(
            checksum="FH",
            raw_telegram="<S1234567890F02D07FH>",
            serial_number="1234567890",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_TYPE_CODE,
        )

        response = self.service.generate_module_type_response(request)

        assert response is not None
        assert "F02D07" in response
        assert "42" in response
        assert response.startswith("<R1234567890F02D0742")
        assert response.endswith(">")

    def test_generate_module_type_response_wrong_function(self):
        """Test module type response with wrong function returns None"""
        request = SystemTelegram(
            checksum="FH",
            raw_telegram="<S1234567890F01D07FH>",
            serial_number="1234567890",
            system_function=SystemFunction.DISCOVERY,  # Wrong function
            datapoint_type=DataPointType.MODULE_TYPE_CODE,
        )

        response = self.service.generate_module_type_response(request)
        assert response is None

    def test_generate_module_type_response_wrong_datapoint(self):
        """Test module type response with wrong data point returns None"""
        request = SystemTelegram(
            checksum="FH",
            raw_telegram="<S1234567890F02D02FH>",
            serial_number="1234567890",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.SW_VERSION,  # Wrong data point
        )

        response = self.service.generate_module_type_response(request)
        assert response is None

    def test_check_request_for_device_matching_serial(self):
        """Test device request check with matching serial"""
        request = SystemTelegram(
            checksum="FH",
            raw_telegram="<S1234567890F02D07FH>",
            serial_number="1234567890",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_TYPE_CODE,
        )

        assert self.service._check_request_for_device(request) is True

    def test_check_request_for_device_broadcast(self):
        """Test device request check with broadcast serial"""
        request = SystemTelegram(
            checksum="FH",
            raw_telegram="<S0000000000F02D07FH>",
            serial_number="0000000000",  # Broadcast
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_TYPE_CODE,
        )

        assert self.service._check_request_for_device(request) is True

    def test_check_request_for_device_different_serial(self):
        """Test device request check with different serial"""
        request = SystemTelegram(
            checksum="FH",
            raw_telegram="<S9999999999F02D07FH>",
            serial_number="9999999999",  # Different serial
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_TYPE_CODE,
        )

        assert self.service._check_request_for_device(request) is False

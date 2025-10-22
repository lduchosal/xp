"""Tests for BaseServerService."""

from unittest.mock import Mock

from xp.models import ModuleTypeCode
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.system_function import SystemFunction
from xp.services.server.base_server_service import BaseServerService


class ConcreteServerService(BaseServerService):
    """Concrete implementation for testing."""

    def __init__(self, serial_number: str):
        """Initialize the concrete server service for testing.

        Args:
            serial_number: Serial number of the device.
        """
        super().__init__(serial_number)
        self.device_type = "TEST"
        self.module_type_code = ModuleTypeCode.XP20
        self.hardware_version = "1.0"
        self.software_version = "2.0"


class TestBaseServerServiceInit:
    """Test BaseServerService initialization."""

    def test_init(self):
        """Test initialization."""
        service = ConcreteServerService("12345")

        assert service.serial_number == "12345"
        assert service.device_type == "TEST"
        assert service.module_type_code == ModuleTypeCode.XP20
        assert service.device_status == "OK"
        assert service.link_number == 1
        assert service.temperature == "+23,5§C"
        assert service.voltage == "+12,5§V"


class TestBaseServerServiceDiscoverResponse:
    """Test discover response generation."""

    def test_generate_discover_response(self):
        """Test generating discover response."""
        response = ConcreteServerService("12345").generate_discover_response()

        assert response.startswith("<R12345F01D")
        assert response.endswith(">")
        assert len(response) >= 14  # Has checksum


class TestBaseServerServiceDatapointResponse:
    """Test datapoint response generation."""

    def test_generate_datapoint_type_response_temperature(self):
        """Test generating temperature datapoint response."""
        response = ConcreteServerService("12345").generate_datapoint_type_response(
            DataPointType.TEMPERATURE
        )

        assert response is not None
        assert "R12345F02" in response
        assert "+23,5§C" in response

    def test_generate_datapoint_type_response_module_type(self):
        """Test generating module type datapoint response."""
        response = ConcreteServerService("12345").generate_datapoint_type_response(
            DataPointType.MODULE_TYPE_CODE
        )

        assert response is not None
        assert "R12345F02" in response
        assert "33" in response  # ModuleTypeCode.XP20.value == 33

    def test_generate_datapoint_type_response_sw_version(self):
        """Test generating software version datapoint response."""
        response = ConcreteServerService("12345").generate_datapoint_type_response(
            DataPointType.SW_VERSION
        )

        assert response is not None
        assert "R12345F02" in response
        assert "2.0" in response

    def test_generate_datapoint_type_response_hw_version(self):
        """Test generating hardware version datapoint response."""
        response = ConcreteServerService("12345").generate_datapoint_type_response(
            DataPointType.HW_VERSION
        )

        assert response is not None
        assert "R12345F02" in response
        assert "1.0" in response

    def test_generate_datapoint_type_response_error_code(self):
        """Test generating error code datapoint response."""
        response = ConcreteServerService("12345").generate_datapoint_type_response(
            DataPointType.MODULE_STATE
        )

        assert response is not None
        assert "R12345F02" in response
        assert "OK" in response

    def test_generate_datapoint_type_response_link_number(self):
        """Test generating link number datapoint response."""
        response = ConcreteServerService("12345").generate_datapoint_type_response(
            DataPointType.LINK_NUMBER
        )

        assert response is not None
        assert "R12345F02" in response
        assert "01" in response  # link_number=1 in hex

    def test_generate_datapoint_type_response_voltage(self):
        """Test generating voltage datapoint response."""
        response = ConcreteServerService("12345").generate_datapoint_type_response(
            DataPointType.VOLTAGE
        )

        assert response is not None
        assert "R12345F02" in response
        assert "+12,5§V" in response


class TestBaseServerServiceRequestChecking:
    """Test request checking methods."""

    def test_check_request_for_device_matching_serial(self):
        """Test checking request with matching serial number."""
        service = ConcreteServerService("12345")
        request = Mock(serial_number="12345")

        result = service._check_request_for_device(request)

        assert result is True

    def test_check_request_for_device_broadcast(self):
        """Test checking broadcast request."""
        service = ConcreteServerService("12345")
        request = Mock(serial_number="0000000000")

        result = service._check_request_for_device(request)

        assert result is True

    def test_check_request_for_device_different_serial(self):
        """Test checking request with different serial number."""
        service = ConcreteServerService("12345")
        request = Mock(serial_number="99999")

        result = service._check_request_for_device(request)

        assert result is False


class TestBaseServerServiceTelegramBuilding:
    """Test telegram building methods."""

    def test_build_response_telegram(self):
        """Test building response telegram with checksum."""
        result = BaseServerService._build_response_telegram("R12345F01D")

        assert result.startswith("<R12345F01D")
        assert result.endswith(">")
        assert len(result) > len("<R12345F01D>")


class TestBaseServerServiceLinkNumber:
    """Test link number setting."""

    def test_set_link_number_success(self):
        """Test setting link number."""
        service = ConcreteServerService("12345")
        request = Mock(
            system_function=SystemFunction.WRITE_CONFIG,
            datapoint_type=DataPointType.LINK_NUMBER,
        )

        response = service.set_link_number(request, 5)

        assert response is not None
        assert "R12345F18D" in response
        assert service.link_number == 5

    def test_set_link_number_wrong_function(self):
        """Test setting link number with wrong function."""
        service = ConcreteServerService("12345")
        request = Mock(
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.LINK_NUMBER,
        )

        response = service.set_link_number(request, 5)

        assert response is None
        assert service.link_number == 1  # Unchanged

    def test_set_link_number_wrong_datapoint(self):
        """Test setting link number with wrong datapoint type."""
        service = ConcreteServerService("12345")
        request = Mock(
            system_function=SystemFunction.WRITE_CONFIG,
            datapoint_type=DataPointType.TEMPERATURE,
        )

        response = service.set_link_number(request, 5)

        assert response is None
        assert service.link_number == 1  # Unchanged


class TestBaseServerServiceProcessSystemTelegram:
    """Test process_system_telegram method."""

    def test_process_system_telegram_not_for_device(self):
        """Test processing telegram not for this device."""
        service = ConcreteServerService("12345")
        request = Mock(serial_number="99999")

        response = service.process_system_telegram(request)

        assert response is None

    def test_process_system_telegram_discovery(self):
        """Test processing discovery request."""
        service = ConcreteServerService("12345")
        request = Mock(serial_number="12345", system_function=SystemFunction.DISCOVERY)

        response = service.process_system_telegram(request)

        assert response is not None
        assert "R12345F01D" in response

    def test_process_system_telegram_read_datapoint(self):
        """Test processing read datapoint request."""
        service = ConcreteServerService("12345")
        request = Mock(
            serial_number="12345",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
        )

        response = service.process_system_telegram(request)

        assert response is not None
        assert "+23,5§C" in response

    def test_process_system_telegram_write_config(self):
        """Test processing write config request."""
        service = ConcreteServerService("12345")
        request = Mock(
            serial_number="12345",
            system_function=SystemFunction.WRITE_CONFIG,
            datapoint_type=DataPointType.LINK_NUMBER,
        )

        response = service.process_system_telegram(request)

        assert response is not None
        assert "R12345F18D" in response

    def test_process_system_telegram_action(self):
        """Test processing action request."""
        service = ConcreteServerService("12345")
        request = Mock(serial_number="12345", system_function=SystemFunction.ACTION)

        response = service.process_system_telegram(request)

        # Default implementation returns None
        assert response is None

    def test_process_system_telegram_unknown_function(self):
        """Test processing request with unknown function."""
        service = ConcreteServerService("12345")
        request = Mock(serial_number="12345", system_function=None)

        response = service.process_system_telegram(request)

        assert response is None


class TestBaseServerServiceHandlers:
    """Test handler methods."""

    def test_handle_device_specific_data_request(self):
        """Test device-specific data request handler."""
        service = ConcreteServerService("12345")
        request = Mock()

        response = service._handle_device_specific_data_request(request)

        assert response is None  # Default implementation

    def test_handle_device_specific_action_request(self):
        """Test device-specific action request handler."""
        service = ConcreteServerService("12345")
        request = Mock()

        response = service._handle_device_specific_action_request(request)

        assert response is None  # Default implementation

    def test_handle_device_specific_config_request(self):
        """Test device-specific config request handler."""
        response = BaseServerService._handle_device_specific_config_request()

        assert response is None  # Default implementation

    def test_handle_return_data_request(self):
        """Test return data request handling."""
        service = ConcreteServerService("12345")
        request = Mock(
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
        )

        response = service._handle_return_data_request(request)

        assert response is not None
        assert "+23,5§C" in response

    def test_handle_return_data_request_no_datapoint(self):
        """Test return data request with no datapoint type."""
        service = ConcreteServerService("12345")
        request = Mock(
            system_function=SystemFunction.READ_DATAPOINT, datapoint_type=None
        )

        response = service._handle_return_data_request(request)

        assert response is None

    def test_handle_write_config_request(self):
        """Test write config request handling."""
        service = ConcreteServerService("12345")
        request = Mock(
            system_function=SystemFunction.WRITE_CONFIG,
            datapoint_type=DataPointType.LINK_NUMBER,
        )

        response = service._handle_write_config_request(request)

        assert response is not None
        assert "F18D" in response

    def test_handle_action_request(self):
        """Test action request handling."""
        service = ConcreteServerService("12345")
        request = Mock(system_function=SystemFunction.ACTION)

        response = service._handle_action_request(request)

        assert response is None  # Default implementation

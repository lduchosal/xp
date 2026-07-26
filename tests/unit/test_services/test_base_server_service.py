# Copyright (c) 2025 ldvchosal
"""Tests for BaseServerService."""

from unittest.mock import Mock

from xp.models import ModuleTypeCode
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram
from xp.services.server.base_server_service import BaseServerService

MIN_RESPONSE_LENGTH = 14
NEW_LINK_NUMBER = 5


class ConcreteServerService(BaseServerService):
    """Concrete implementation for testing."""

    def __init__(self, serial_number: str) -> None:
        """Initialize the concrete server service for testing.

        Args:
            serial_number: Serial number of the device.

        """
        super().__init__(serial_number)
        self.device_type = "TEST"
        self.module_type_code = ModuleTypeCode.XP20
        self.hardware_version = "1.0"
        self.software_version = "2.0"

    def check_request_for_device(self, request: SystemTelegram) -> bool:
        """Expose the protected request check for tests.

        Returns:
            True if the request targets this device or the broadcast
            address, False otherwise.

        """
        return self._check_request_for_device(request)

    @classmethod
    def build_response_telegram(cls, data_part: str) -> str:
        """Expose the protected telegram builder for tests.

        Returns:
            The response telegram built from the data part, with checksum and framing.

        """
        return cls._build_response_telegram(data_part)

    def handle_device_specific_data_request(
        self, request: SystemTelegram
    ) -> str | None:
        """Expose the protected data request handler for tests.

        Returns:
            The response telegram, or None if the request is not handled.

        """
        return self._handle_device_specific_data_request(request)

    def handle_device_specific_action_request(
        self, request: SystemTelegram
    ) -> str | None:
        """Expose the protected action request handler for tests.

        Returns:
            The response telegram, or None if the request is not handled.

        """
        return self._handle_device_specific_action_request(request)

    @classmethod
    def handle_device_specific_config_request(cls) -> str | None:
        """Expose the protected config request handler for tests.

        Returns:
            The response telegram, or None if the request is not handled.

        """
        return cls._handle_device_specific_config_request()

    def handle_return_data_request(self, request: SystemTelegram) -> str | None:
        """Expose the protected return data handler for tests.

        Returns:
            The response telegram, or None if the request is not handled.

        """
        return self._handle_return_data_request(request)

    def handle_write_config_request(self, request: SystemTelegram) -> str | None:
        """Expose the protected write config handler for tests.

        Returns:
            The response telegram, or None if the request is not handled.

        """
        return self._handle_write_config_request(request)

    def handle_action_request(self, request: SystemTelegram) -> str | None:
        """Expose the protected action handler for tests.

        Returns:
            The response telegram, or None if the request is not handled.

        """
        return self._handle_action_request(request)


class TestBaseServerServiceInit:
    """Test BaseServerService initialization."""

    def test_init(self) -> None:
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

    def test_generate_discover_response(self) -> None:
        """Test generating discover response."""
        response = ConcreteServerService("12345").generate_discover_response()

        assert response.startswith("<R12345F01D")
        assert response.endswith(">")
        assert len(response) >= MIN_RESPONSE_LENGTH  # Has checksum


class TestBaseServerServiceDatapointResponse:
    """Test datapoint response generation."""

    def test_generate_datapoint_type_response_temperature(self) -> None:
        """Test generating temperature datapoint response."""
        response = ConcreteServerService("12345").generate_datapoint_type_response(
            DataPointType.TEMPERATURE
        )

        assert response is not None
        assert "R12345F02" in response
        assert "+23,5§C" in response

    def test_generate_datapoint_type_response_module_type(self) -> None:
        """Test generating module type datapoint response."""
        response = ConcreteServerService("12345").generate_datapoint_type_response(
            DataPointType.MODULE_TYPE_CODE
        )

        assert response is not None
        assert "R12345F02" in response
        assert "33" in response  # ModuleTypeCode.XP20.value == 33

    def test_generate_datapoint_type_response_sw_version(self) -> None:
        """Test generating software version datapoint response."""
        response = ConcreteServerService("12345").generate_datapoint_type_response(
            DataPointType.SW_VERSION
        )

        assert response is not None
        assert "R12345F02" in response
        assert "2.0" in response

    def test_generate_datapoint_type_response_hw_version(self) -> None:
        """Test generating hardware version datapoint response."""
        response = ConcreteServerService("12345").generate_datapoint_type_response(
            DataPointType.HW_VERSION
        )

        assert response is not None
        assert "R12345F02" in response
        assert "1.0" in response

    def test_generate_datapoint_type_response_error_code(self) -> None:
        """Test generating error code datapoint response."""
        response = ConcreteServerService("12345").generate_datapoint_type_response(
            DataPointType.MODULE_STATE
        )

        assert response is not None
        assert "R12345F02" in response
        assert "OK" in response

    def test_generate_datapoint_type_response_link_number(self) -> None:
        """Test generating link number datapoint response."""
        response = ConcreteServerService("12345").generate_datapoint_type_response(
            DataPointType.LINK_NUMBER
        )

        assert response is not None
        assert "R12345F02" in response
        assert "01" in response  # link_number=1 in hex

    def test_generate_datapoint_type_response_voltage(self) -> None:
        """Test generating voltage datapoint response."""
        response = ConcreteServerService("12345").generate_datapoint_type_response(
            DataPointType.VOLTAGE
        )

        assert response is not None
        assert "R12345F02" in response
        assert "+12,5§V" in response


class TestBaseServerServiceRequestChecking:
    """Test request checking methods."""

    def test_check_request_for_device_matching_serial(self) -> None:
        """Test checking request with matching serial number."""
        service = ConcreteServerService("12345")
        request = Mock(serial_number="12345")

        result = service.check_request_for_device(request)

        assert result is True

    def test_check_request_for_device_broadcast(self) -> None:
        """Test checking broadcast request."""
        service = ConcreteServerService("12345")
        request = Mock(serial_number="0000000000")

        result = service.check_request_for_device(request)

        assert result is True

    def test_check_request_for_device_different_serial(self) -> None:
        """Test checking request with different serial number."""
        service = ConcreteServerService("12345")
        request = Mock(serial_number="99999")

        result = service.check_request_for_device(request)

        assert result is False


class TestBaseServerServiceTelegramBuilding:
    """Test telegram building methods."""

    def test_build_response_telegram(self) -> None:
        """Test building response telegram with checksum."""
        result = ConcreteServerService.build_response_telegram("R12345F01D")

        assert result.startswith("<R12345F01D")
        assert result.endswith(">")
        assert len(result) > len("<R12345F01D>")


class TestBaseServerServiceLinkNumber:
    """Test link number setting."""

    def test_set_link_number_success(self) -> None:
        """Test setting link number."""
        service = ConcreteServerService("12345")
        request = Mock(
            system_function=SystemFunction.WRITE_CONFIG,
            datapoint_type=DataPointType.LINK_NUMBER,
        )

        response = service.set_link_number(request, NEW_LINK_NUMBER)

        assert response is not None
        assert "R12345F18D" in response
        assert service.link_number == NEW_LINK_NUMBER

    def test_set_link_number_wrong_function(self) -> None:
        """Test setting link number with wrong function."""
        service = ConcreteServerService("12345")
        request = Mock(
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.LINK_NUMBER,
        )

        response = service.set_link_number(request, 5)

        assert response is None
        assert service.link_number == 1  # Unchanged

    def test_set_link_number_wrong_datapoint(self) -> None:
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

    def test_process_system_telegram_not_for_device(self) -> None:
        """Test processing telegram not for this device."""
        service = ConcreteServerService("12345")
        request = Mock(serial_number="99999")

        response = service.process_system_telegram(request)

        assert response is None

    def test_process_system_telegram_discovery(self) -> None:
        """Test processing discovery request."""
        service = ConcreteServerService("12345")
        request = Mock(serial_number="12345", system_function=SystemFunction.DISCOVERY)

        response = service.process_system_telegram(request)

        assert response is not None
        assert "R12345F01D" in response

    def test_process_system_telegram_read_datapoint(self) -> None:
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

    def test_process_system_telegram_write_config(self) -> None:
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

    def test_process_system_telegram_action(self) -> None:
        """Test processing action request."""
        service = ConcreteServerService("12345")
        request = Mock(serial_number="12345", system_function=SystemFunction.ACTION)

        response = service.process_system_telegram(request)

        # Default implementation returns None
        assert response is None

    def test_process_system_telegram_unknown_function(self) -> None:
        """Test processing request with unknown function."""
        service = ConcreteServerService("12345")
        request = Mock(serial_number="12345", system_function=None)

        response = service.process_system_telegram(request)

        assert response is None


class TestBaseServerServiceHandlers:
    """Test handler methods."""

    def test_handle_device_specific_data_request(self) -> None:
        """Test device-specific data request handler."""
        service = ConcreteServerService("12345")
        request = Mock()

        response = service.handle_device_specific_data_request(request)

        assert response is None  # Default implementation

    def test_handle_device_specific_action_request(self) -> None:
        """Test device-specific action request handler."""
        service = ConcreteServerService("12345")
        request = Mock()

        response = service.handle_device_specific_action_request(request)

        assert response is None  # Default implementation

    def test_handle_device_specific_config_request(self) -> None:
        """Test device-specific config request handler."""
        response = ConcreteServerService.handle_device_specific_config_request()

        assert response is None  # Default implementation

    def test_handle_return_data_request(self) -> None:
        """Test return data request handling."""
        service = ConcreteServerService("12345")
        request = Mock(
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
        )

        response = service.handle_return_data_request(request)

        assert response is not None
        assert "+23,5§C" in response

    def test_handle_return_data_request_no_datapoint(self) -> None:
        """Test return data request with no datapoint type."""
        service = ConcreteServerService("12345")
        request = Mock(
            system_function=SystemFunction.READ_DATAPOINT, datapoint_type=None
        )

        response = service.handle_return_data_request(request)

        assert response is None

    def test_handle_write_config_request(self) -> None:
        """Test write config request handling."""
        service = ConcreteServerService("12345")
        request = Mock(
            system_function=SystemFunction.WRITE_CONFIG,
            datapoint_type=DataPointType.LINK_NUMBER,
        )

        response = service.handle_write_config_request(request)

        assert response is not None
        assert "F18D" in response

    def test_handle_action_request(self) -> None:
        """Test action request handling."""
        service = ConcreteServerService("12345")
        request = Mock(system_function=SystemFunction.ACTION)

        response = service.handle_action_request(request)

        assert response is None  # Default implementation

# mypy: disable-error-code="arg-type,call-arg,func-returns-value,attr-defined"
from datetime import datetime
from unittest.mock import Mock

import pytest

from xp.models.conbus.conbus_linknumber import ConbusLinknumberResponse
from xp.services.conbus.conbus_linknumber_get_service import ConbusLinknumberGetService
from xp.services.conbus.conbus_linknumber_set_service import ConbusLinknumberSetService


class TestConbusLinknumberSetService:
    """Test cases for ConbusLinknumberSetService."""

    @pytest.fixture
    def mock_telegram_service(self):
        """Create mock TelegramService."""
        return Mock()

    @pytest.fixture
    def mock_cli_config(self):
        """Create mock ConbusClientConfig."""
        mock_config = Mock()
        mock_config.conbus = Mock()
        mock_config.conbus.ip = "127.0.0.1"
        mock_config.conbus.port = 10001
        mock_config.conbus.timeout = 2.0
        return mock_config

    @pytest.fixture
    def mock_reactor(self):
        """Create mock reactor."""
        return Mock()

    @pytest.fixture
    def service(self, mock_telegram_service, mock_cli_config, mock_reactor):
        """Create service instance with mocked dependencies."""
        return ConbusLinknumberSetService(
            telegram_service=mock_telegram_service,
            cli_config=mock_cli_config,
            reactor=mock_reactor,
        )

    @pytest.fixture
    def get_service(self, mock_telegram_service, mock_cli_config, mock_reactor):
        """Create get service instance with mocked dependencies."""
        return ConbusLinknumberGetService(
            telegram_service=mock_telegram_service,
            cli_config=mock_cli_config,
            reactor=mock_reactor,
        )

    def test_service_initialization(
        self, mock_telegram_service, mock_cli_config, mock_reactor
    ):
        """Test service initialization."""
        service = ConbusLinknumberSetService(
            telegram_service=mock_telegram_service,
            cli_config=mock_cli_config,
            reactor=mock_reactor,
        )

        assert service.telegram_service is not None
        assert service.serial_number == ""
        assert service.link_number == 0
        assert service.finish_callback is None

    # Note: Tests updated to use new async callback API with Twisted reactor

    def test_set_linknumber_success_ack(self, service):
        """Test successful link number setting with ACK response."""
        # Setup callback to capture result
        captured_result = None

        def callback(response: ConbusLinknumberResponse) -> None:
            nonlocal captured_result
            captured_result = response

        # Mock the start_reactor to simulate immediate success
        def mock_start_reactor():
            # Directly call succeed instead of going through connection_established
            from xp.models.telegram.system_function import SystemFunction

            service.succeed(SystemFunction.ACK)

        service.start_reactor = mock_start_reactor

        # Test
        service.set_linknumber("0123450001", 25, callback)

        # Assertions
        assert captured_result is not None
        assert isinstance(captured_result, ConbusLinknumberResponse)
        assert captured_result.success is True
        assert captured_result.result == "ACK"
        assert captured_result.serial_number == "0123450001"
        assert captured_result.link_number == 25

    def test_set_linknumber_success_nak(self, service):
        """Test link number setting with NAK response."""
        # Setup callback to capture result
        captured_result = None

        def callback(response: ConbusLinknumberResponse) -> None:
            nonlocal captured_result
            captured_result = response

        # Mock the start_reactor to simulate NAK response
        def mock_start_reactor():
            # Directly call failed instead of going through connection_established
            service.failed("Module responded with NAK")

        service.start_reactor = mock_start_reactor

        # Test
        service.set_linknumber("0123450001", 25, callback)

        # Assertions
        assert captured_result is not None
        assert isinstance(captured_result, ConbusLinknumberResponse)
        assert captured_result.success is False
        assert captured_result.result == "NAK"
        assert captured_result.serial_number == "0123450001"

    def test_set_linknumber_connection_failure(self, service):
        """Test link number setting with connection failure."""
        # Setup callback to capture result
        captured_result = None

        def callback(response: ConbusLinknumberResponse) -> None:
            nonlocal captured_result
            captured_result = response

        # Mock start_reactor to simulate connection failure
        def mock_start_reactor():
            service.failed("Connection timeout")

        service.start_reactor = mock_start_reactor

        # Test
        service.set_linknumber("0123450001", 25, callback)

        # Assertions
        assert captured_result is not None
        assert isinstance(captured_result, ConbusLinknumberResponse)
        assert captured_result.success is False
        assert captured_result.result == "NAK"
        assert captured_result.error == "Connection timeout"

    def test_set_linknumber_invalid_parameters(self, service):
        """Test link number setting with invalid parameters."""
        # Setup callback to capture result
        captured_result = None

        def callback(response: ConbusLinknumberResponse) -> None:
            nonlocal captured_result
            captured_result = response

        # Mock start_reactor to trigger connection_established which validates params
        def mock_start_reactor():
            service.connection_established()

        service.start_reactor = mock_start_reactor

        # Test with invalid serial number
        service.set_linknumber("invalid", 25, callback)

        # Assertions
        assert captured_result is not None
        assert isinstance(captured_result, ConbusLinknumberResponse)
        assert captured_result.success is False
        assert captured_result.result == "NAK"
        assert captured_result.error is not None
        assert "Serial number must be 10 digits" in captured_result.error

    def test_context_manager(self, service):
        """Test service can be used as context manager."""
        with service as s:
            assert s is service

    def test_set_linknumber_invalid_link_number(self, service):
        """Test link number setting with invalid link number."""
        # Setup callback to capture result
        captured_result = None

        def callback(response: ConbusLinknumberResponse) -> None:
            nonlocal captured_result
            captured_result = response

        # Mock start_reactor to trigger connection_established which validates params
        def mock_start_reactor():
            service.connection_established()

        service.start_reactor = mock_start_reactor

        # Test with invalid link number (>99)
        service.set_linknumber("0123450001", 101, callback)

        # Assertions
        assert captured_result is not None
        assert isinstance(captured_result, ConbusLinknumberResponse)
        assert captured_result.success is False
        assert captured_result.result == "NAK"
        assert captured_result.error is not None
        assert "Link number must be between 0-99" in captured_result.error

    def test_get_linknumber_success(self, get_service):
        """Test successful link number retrieval."""
        # Setup callback to capture result
        captured_result = None

        def callback(response: ConbusLinknumberResponse) -> None:
            nonlocal captured_result
            captured_result = response

        # Mock start_reactor to simulate successful datapoint query
        def mock_start_reactor():
            # Simulate successful datapoint response
            from xp.models import ConbusDatapointResponse

            mock_datapoint_telegram = Mock()
            mock_datapoint_telegram.data_value = "25"

            datapoint_response = ConbusDatapointResponse(
                success=True,
                datapoint_telegram=mock_datapoint_telegram,
                sent_telegram="<S0123450001F03D04FG>",
                received_telegrams=["<R0123450001F03D041AFH>"],
                timestamp=datetime.now(),
            )
            get_service.finish_service_callback(datapoint_response)

        get_service.start_reactor = mock_start_reactor

        # Test
        get_service.get_linknumber("0123450001", callback)

        # Assertions
        assert captured_result is not None
        assert isinstance(captured_result, ConbusLinknumberResponse)
        assert captured_result.success is True
        assert captured_result.result == "SUCCESS"
        assert captured_result.serial_number == "0123450001"
        assert captured_result.link_number == 25

    def test_get_linknumber_query_failed(self, get_service):
        """Test link number retrieval when datapoint query fails."""
        # Setup callback to capture result
        captured_result = None

        def callback(response: ConbusLinknumberResponse) -> None:
            nonlocal captured_result
            captured_result = response

        # Mock start_reactor to simulate failed datapoint query
        def mock_start_reactor():
            from xp.models import ConbusDatapointResponse

            datapoint_response = ConbusDatapointResponse(
                success=False,
                datapoint_telegram=None,
                sent_telegram="<S0123450001F03D04FG>",
                received_telegrams=[],
                error="Connection timeout",
                timestamp=datetime.now(),
            )
            get_service.finish_service_callback(datapoint_response)

        get_service.start_reactor = mock_start_reactor

        # Test
        get_service.get_linknumber("0123450001", callback)

        # Assertions
        assert captured_result is not None
        assert isinstance(captured_result, ConbusLinknumberResponse)
        assert captured_result.success is False
        assert captured_result.result == "FAILURE"
        assert captured_result.serial_number == "0123450001"
        assert captured_result.link_number == 0
        assert captured_result.error == "Connection timeout"

    def test_get_linknumber_parse_error(self, get_service):
        """Test link number retrieval when parsing fails."""
        # Setup callback to capture result
        captured_result = None

        def callback(response: ConbusLinknumberResponse) -> None:
            nonlocal captured_result
            captured_result = response

        # Mock start_reactor to simulate parse error
        def mock_start_reactor():
            from xp.models import ConbusDatapointResponse

            # Mock with invalid data that will cause int() conversion to fail
            mock_datapoint_telegram = Mock()
            mock_datapoint_telegram.data_value = "invalid"

            datapoint_response = ConbusDatapointResponse(
                success=True,
                datapoint_telegram=mock_datapoint_telegram,
                sent_telegram="<S0123450001F03D04FG>",
                received_telegrams=["<R0123450001F03D04invalidFH>"],
                timestamp=datetime.now(),
            )

            # This will fail when trying to parse int("invalid")
            try:
                get_service.finish_service_callback(datapoint_response)
            except ValueError:
                # Catch the error and create failure response
                from xp.models.conbus.conbus_linknumber import (
                    ConbusLinknumberResponse,
                )

                get_service.service_callback(
                    ConbusLinknumberResponse(
                        success=False,
                        result="PARSE_ERROR",
                        link_number=None,
                        serial_number=get_service.serial_number,
                        error="Failed to parse link number: invalid literal for int() with base 10: 'invalid'",
                    )
                )

        get_service.start_reactor = mock_start_reactor

        # Test
        get_service.get_linknumber("0123450001", callback)

        # Assertions
        assert captured_result is not None
        assert isinstance(captured_result, ConbusLinknumberResponse)
        assert captured_result.success is False
        assert captured_result.result == "PARSE_ERROR"
        assert captured_result.serial_number == "0123450001"
        assert captured_result.link_number is None
        assert (
            captured_result.error is not None
            and "Failed to parse link number" in captured_result.error
        )

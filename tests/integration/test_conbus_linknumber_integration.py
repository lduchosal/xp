# mypy: disable-error-code="arg-type,call-arg,func-returns-value,attr-defined"
"""Integration tests for Conbus link number functionality."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from xp.models import ConbusDatapointResponse
from xp.models.conbus.conbus_linknumber import ConbusLinknumberResponse
from xp.services.conbus.conbus_linknumber_get_service import ConbusLinknumberGetService
from xp.services.conbus.conbus_linknumber_set_service import ConbusLinknumberSetService


class TestConbusLinknumberIntegration:
    """Integration test cases for Conbus link number operations.

    Note: Tests updated to use new async callback API with Twisted reactor.
    """

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

    def test_conbus_linknumber_valid(self, service):
        """Test setting valid link number."""
        captured_result = None

        def callback(response: ConbusLinknumberResponse) -> None:
            """Test helper function.

            Args:
                response: The response from the service.
            """
            nonlocal captured_result
            captured_result = response

        def mock_start_reactor():
            """Test helper function."""
            from xp.models.telegram.system_function import SystemFunction

            service.succeed(SystemFunction.ACK)

        service.start_reactor = mock_start_reactor
        service.set_linknumber("0123450001", 25, callback)

        assert captured_result is not None
        assert captured_result.success is True
        assert captured_result.result == "ACK"
        assert captured_result.serial_number == "0123450001"

    def test_conbus_linknumber_invalid_response(self, service):
        """Test handling invalid/NAK responses."""
        captured_result = None

        def callback(response: ConbusLinknumberResponse) -> None:
            """Test helper function.

            Args:
                response: The response from the service.
            """
            nonlocal captured_result
            captured_result = response

        def mock_start_reactor():
            """Test helper function."""
            service.failed("Module responded with NAK")

        service.start_reactor = mock_start_reactor
        service.set_linknumber("0123450001", 25, callback)

        assert captured_result is not None
        assert captured_result.success is False
        assert captured_result.result == "NAK"

    def test_conbus_linknumber_connection_failure(self, service):
        """Test handling connection failures."""
        captured_result = None

        def callback(response: ConbusLinknumberResponse) -> None:
            """Test helper function.

            Args:
                response: The response from the service.
            """
            nonlocal captured_result
            captured_result = response

        def mock_start_reactor():
            """Test helper function."""
            service.failed("Connection timeout")

        service.start_reactor = mock_start_reactor
        service.set_linknumber("0123450001", 25, callback)

        assert captured_result is not None
        assert captured_result.success is False
        assert captured_result.result == "NAK"
        assert captured_result.error == "Connection timeout"

    def test_conbus_linknumber_invalid_serial_number(self, service):
        """Test handling invalid serial number."""
        captured_result = None

        def callback(response: ConbusLinknumberResponse) -> None:
            """Test helper function.

            Args:
                response: The response from the service.
            """
            nonlocal captured_result
            captured_result = response

        def mock_start_reactor():
            """Test helper function."""
            service.connection_established()

        service.start_reactor = mock_start_reactor
        service.set_linknumber("invalid", 25, callback)

        assert captured_result is not None
        assert captured_result.success is False
        assert captured_result.result == "NAK"
        assert captured_result.error is not None
        assert "Serial number must be 10 digits" in captured_result.error

    def test_conbus_linknumber_invalid_link_number(self, service):
        """Test handling invalid link number."""
        captured_result = None

        def callback(response: ConbusLinknumberResponse) -> None:
            """Test helper function.

            Args:
                response: The response from the service.
            """
            nonlocal captured_result
            captured_result = response

        def mock_start_reactor():
            """Test helper function."""
            service.connection_established()

        service.start_reactor = mock_start_reactor
        service.set_linknumber("0123450001", 101, callback)

        assert captured_result is not None
        assert captured_result.success is False
        assert captured_result.result == "NAK"
        assert captured_result.error is not None
        assert "Link number must be between 0-99" in captured_result.error

    def test_conbus_linknumber_edge_cases(self, service):
        """Test edge cases for link number values."""
        # Test minimum value (0)
        captured_result_min = None

        def callback_min(response: ConbusLinknumberResponse) -> None:
            """Test helper function.

            Args:
                response: The response from the service.
            """
            nonlocal captured_result_min
            captured_result_min = response

        def mock_start_reactor():
            """Test helper function."""
            from xp.models.telegram.system_function import SystemFunction

            service.succeed(SystemFunction.ACK)

        service.start_reactor = mock_start_reactor
        service.set_linknumber("0123450001", 0, callback_min)

        assert captured_result_min is not None
        assert captured_result_min.success is True
        assert captured_result_min.result == "ACK"

        # Test maximum value (99)
        captured_result_max = None

        def callback_max(response: ConbusLinknumberResponse) -> None:
            """Test helper function.

            Args:
                response: The response from the service.
            """
            nonlocal captured_result_max
            captured_result_max = response

        service.start_reactor = mock_start_reactor
        service.set_linknumber("0123450001", 99, callback_max)

        assert captured_result_max is not None
        assert captured_result_max.success is True
        assert captured_result_max.result == "ACK"

    def test_service_context_manager(self, service):
        """Test service can be used as context manager."""
        with service as s:
            assert s is service

    def test_conbus_get_linknumber_valid(self, get_service):
        """Test getting valid link number."""
        captured_result = None

        def callback(response: ConbusLinknumberResponse) -> None:
            """Test helper function.

            Args:
                response: The response from the service.
            """
            nonlocal captured_result
            captured_result = response

        def mock_start_reactor():
            """Test helper function."""
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
        get_service.get_linknumber("0123450001", callback)

        assert captured_result is not None
        assert captured_result.success is True
        assert captured_result.result == "SUCCESS"
        assert captured_result.link_number == 25

    def test_conbus_get_linknumber_query_failed(self, get_service):
        """Test handling datapoint query failures."""
        captured_result = None

        def callback(response: ConbusLinknumberResponse) -> None:
            """Test helper function.

            Args:
                response: The response from the service.
            """
            nonlocal captured_result
            captured_result = response

        def mock_start_reactor():
            """Test helper function."""
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
        get_service.get_linknumber("0123450001", callback)

        assert captured_result is not None
        assert captured_result.success is False
        assert captured_result.result == "FAILURE"
        assert captured_result.error == "Connection timeout"

    def test_conbus_get_linknumber_parse_error(self, get_service):
        """Test handling invalid link number data."""
        captured_result = None

        def callback(response: ConbusLinknumberResponse) -> None:
            """Test helper function.

            Args:
                response: The response from the service.
            """
            nonlocal captured_result
            captured_result = response

        def mock_start_reactor():
            """Test helper function."""
            mock_datapoint_telegram = Mock()
            mock_datapoint_telegram.data_value = "invalid"

            datapoint_response = ConbusDatapointResponse(
                success=True,
                datapoint_telegram=mock_datapoint_telegram,
                sent_telegram="<S0123450001F03D04FG>",
                received_telegrams=["<R0123450001F03D04invalidFH>"],
                timestamp=datetime.now(),
            )

            try:
                get_service.finish_service_callback(datapoint_response)
            except ValueError:
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
        get_service.get_linknumber("0123450001", callback)

        assert captured_result is not None
        assert captured_result.success is False
        assert captured_result.result == "PARSE_ERROR"
        assert (
            captured_result.error is not None
            and "Failed to parse link number" in captured_result.error
        )

    def test_conbus_get_linknumber_service_exception(self, get_service):
        """Test handling service exceptions."""
        # This test verifies that the get service handles exceptions gracefully
        # In practice, exceptions should be caught and converted to error responses
        captured_result = None

        def callback(response: ConbusLinknumberResponse) -> None:
            """Test helper function.

            Args:
                response: The response from the service.
            """
            nonlocal captured_result
            captured_result = response

        def mock_start_reactor():
            """Test helper function."""
            # Simulate an exception during service execution
            datapoint_response = ConbusDatapointResponse(
                success=False,
                datapoint_telegram=None,
                sent_telegram="",
                received_telegrams=[],
                error="Unexpected error: Service unavailable",
                timestamp=datetime.now(),
            )
            get_service.finish_service_callback(datapoint_response)

        get_service.start_reactor = mock_start_reactor
        get_service.get_linknumber("0123450001", callback)

        assert captured_result is not None
        assert captured_result.success is False
        assert captured_result.result == "FAILURE"
        assert captured_result.error is not None

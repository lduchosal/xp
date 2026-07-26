# Copyright (c) 2025 ldvchosal
"""Tests for CLI decorators."""

from typing import Never

import click
import pytest
from click.testing import CliRunner

from xp.cli.utils.decorators import (
    common_options,
    connection_command,
    file_operation_command,
    handle_service_errors,
    list_command,
    require_arguments,
    service_command,
    telegram_parser_command,
    with_formatter,
)
from xp.cli.utils.formatters import OutputFormatter, TelegramFormatter
from xp.services.telegram.telegram_service import TelegramParsingError


class CustomError(Exception):
    """Custom error for testing."""


class TestHandleServiceErrors:
    """Test handle_service_errors decorator."""

    def test_successful_execution(self) -> None:
        """Test decorator allows successful execution."""

        @handle_service_errors(ValueError)
        def test_func() -> str:
            return "success"

        result = test_func()
        assert result == "success"

    def test_handles_specified_exception(self) -> None:
        """Test decorator handles specified service exception."""

        @handle_service_errors(ValueError)
        def test_func() -> Never:
            msg = "Test error"
            raise ValueError(msg)

        runner = CliRunner()
        with runner.isolated_filesystem():
            with pytest.raises(SystemExit) as exc_info:
                test_func()
            assert exc_info.value.code == 1

    def test_handles_multiple_exceptions(self) -> None:
        """Test decorator handles multiple exception types."""

        @handle_service_errors(ValueError, TypeError)
        def test_func(error_type: str) -> Never:
            if error_type == "value":
                msg = "Value error"
                raise ValueError(msg)
            msg = "Type error"
            raise TypeError(msg)

        with pytest.raises(SystemExit):
            test_func("value")

        with pytest.raises(SystemExit):
            test_func("type")

    def test_handles_unexpected_exception(self) -> None:
        """Test decorator handles unexpected exceptions."""

        @handle_service_errors(ValueError)
        def test_func() -> Never:
            msg = "Unexpected error"
            raise RuntimeError(msg)

        with pytest.raises(SystemExit) as exc_info:
            test_func()
        assert exc_info.value.code == 1

    def test_error_message_format(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test error message is properly formatted."""

        @handle_service_errors(ValueError)
        def test_func() -> Never:
            msg = "Test error message"
            raise ValueError(msg)

        with pytest.raises(SystemExit):
            test_func()

        captured = capsys.readouterr()
        assert "Test error message" in captured.out
        assert "error" in captured.out.lower()


class TestCommonOptions:
    """Test common_options decorator."""

    def test_common_options_passes_through(self) -> None:
        """Test common_options decorator passes function through."""

        @common_options
        def test_func() -> str:
            return "result"

        result = test_func()
        assert result == "result"


class TestTelegramParserCommand:
    """Test telegram_parser_command decorator."""

    def test_successful_execution(self) -> None:
        """Test decorator allows successful execution."""

        @telegram_parser_command()
        def test_func() -> str:
            return "success"

        result = test_func()
        assert result == "success"

    def test_handles_telegram_parsing_error(self) -> None:
        """Test decorator handles TelegramParsingError."""

        @telegram_parser_command()
        def test_func() -> Never:
            msg = "Invalid telegram format"
            raise TelegramParsingError(msg)

        with pytest.raises(SystemExit) as exc_info:
            test_func()
        assert exc_info.value.code == 1

    def test_handles_additional_service_exceptions(self) -> None:
        """Test decorator handles additional service exceptions."""

        @telegram_parser_command(service_exceptions=(CustomError,))
        def test_func() -> Never:
            msg = "Custom error"
            raise CustomError(msg)

        with pytest.raises(SystemExit) as exc_info:
            test_func()
        assert exc_info.value.code == 1


class TestServiceCommand:
    """Test service_command decorator."""

    def test_successful_execution(self) -> None:
        """Test decorator allows successful execution."""

        @service_command(ValueError)
        def test_func() -> str:
            return "success"

        result = test_func()
        assert result == "success"

    def test_handles_service_exception(self) -> None:
        """Test decorator handles service exceptions."""

        @service_command(ValueError)
        def test_func() -> Never:
            msg = "Service error"
            raise ValueError(msg)

        with pytest.raises(SystemExit) as exc_info:
            test_func()
        assert exc_info.value.code == 1


class TestListCommand:
    """Test list_command decorator."""

    def test_successful_execution(self) -> None:
        """Test decorator allows successful execution."""

        @list_command(ValueError)
        def test_func() -> list[str]:
            return ["item1", "item2"]

        result = test_func()
        assert result == ["item1", "item2"]

    def test_handles_service_exception(self) -> None:
        """Test decorator handles service exceptions."""

        @list_command(ValueError)
        def test_func() -> Never:
            msg = "List error"
            raise ValueError(msg)

        with pytest.raises(SystemExit) as exc_info:
            test_func()
        assert exc_info.value.code == 1


class TestFileOperationCommand:
    """Test file_operation_command decorator."""

    def test_adds_time_range_option(self) -> None:
        """Test decorator adds time-range option."""

        @click.command()
        @file_operation_command()
        def test_cmd(time_range: str, **_kwargs: object) -> None:
            click.echo(f"time_range={time_range}")

        result = CliRunner().invoke(
            test_cmd, ["--time-range", "00:00:00,000-01:00:00,000"]
        )
        assert result.exit_code == 0
        assert "time_range=00:00:00,000-01:00:00,000" in result.output

    def test_adds_filter_direction_option(self) -> None:
        """Test decorator adds filter-direction option."""

        @click.command()
        @file_operation_command()
        def test_cmd(filter_direction: str, **_kwargs: object) -> None:
            click.echo(f"filter_direction={filter_direction}")

        result = CliRunner().invoke(test_cmd, ["--filter-direction", "tx"])
        assert result.exit_code == 0
        assert "filter_direction=tx" in result.output

    def test_adds_filter_type_option(self) -> None:
        """Test decorator adds filter-type option."""

        @click.command()
        @file_operation_command()
        def test_cmd(filter_type: str, **_kwargs: object) -> None:
            click.echo(f"filter_type={filter_type}")

        result = CliRunner().invoke(test_cmd, ["--filter-type", "event"])
        assert result.exit_code == 0
        assert "filter_type=event" in result.output

    def test_filter_direction_validates_choices(self) -> None:
        """Test filter-direction validates allowed choices."""

        @click.command()
        @file_operation_command()
        def test_cmd(filter_direction: str, **_kwargs: object) -> None:
            click.echo(f"filter_direction={filter_direction}")

        result = CliRunner().invoke(test_cmd, ["--filter-direction", "invalid"])
        assert result.exit_code != 0
        assert "Invalid value" in result.output or "invalid" in result.output.lower()

    def test_filter_type_validates_choices(self) -> None:
        """Test filter-type validates allowed choices."""

        @click.command()
        @file_operation_command()
        def test_cmd(filter_type: str, **_kwargs: object) -> None:
            click.echo(f"filter_type={filter_type}")

        result = CliRunner().invoke(test_cmd, ["--filter-type", "invalid"])
        assert result.exit_code != 0


class TestWithFormatter:
    """Test with_formatter decorator."""

    def test_injects_default_formatter(self) -> None:
        """Test decorator injects default formatter."""

        @with_formatter()
        def test_func(formatter: OutputFormatter | None = None) -> OutputFormatter:
            assert formatter is not None
            assert isinstance(formatter, OutputFormatter)
            return formatter

        formatter = test_func()
        assert formatter.json_output is True

    def test_injects_custom_formatter(self) -> None:
        """Test decorator injects custom formatter class."""

        @with_formatter(formatter_class=TelegramFormatter)
        def test_func(formatter: TelegramFormatter | None = None) -> TelegramFormatter:
            assert formatter is not None
            assert isinstance(formatter, TelegramFormatter)
            return formatter

        formatter = test_func()
        assert formatter.json_output is True

    def test_formatter_passed_as_kwarg(self) -> None:
        """Test formatter is passed as keyword argument."""

        @with_formatter()
        def test_func(**kwargs: object) -> object:
            assert "formatter" in kwargs
            return kwargs["formatter"]

        formatter = test_func()
        assert isinstance(formatter, OutputFormatter)


class TestRequireArguments:
    """Test require_arguments decorator."""

    def test_successful_execution_with_args(self) -> None:
        """Test decorator allows execution with all required args."""

        @require_arguments("arg1", "arg2")
        def test_func(arg1: str | None = None, arg2: str | None = None) -> str:
            return f"{arg1}-{arg2}"

        result = test_func(arg1="value1", arg2="value2")
        assert result == "value1-value2"

    def test_fails_with_missing_argument(self) -> None:
        """Test decorator fails with missing required argument."""

        @require_arguments("arg1", "arg2")
        def test_func(arg1: str | None = None, arg2: str | None = None) -> str:
            return f"{arg1}-{arg2}"

        with pytest.raises(SystemExit) as exc_info:
            test_func(arg1="value1", arg2=None)
        assert exc_info.value.code == 1

    def test_error_message_for_missing_args(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test error message lists missing arguments."""

        @require_arguments("arg1", "arg2")
        def test_func(arg1: str | None = None, arg2: str | None = None) -> str:
            return f"{arg1}-{arg2}"

        with pytest.raises(SystemExit):
            test_func(arg1=None, arg2=None)

        captured = capsys.readouterr()
        assert "Missing required arguments" in captured.out
        assert "arg1" in captured.out
        assert "arg2" in captured.out


class TestConnectionCommand:
    """Test connection_command decorator."""

    def test_successful_execution(self) -> None:
        """Test decorator allows successful execution."""

        @connection_command()
        def test_func() -> str:
            return "connected"

        result = test_func()
        assert result == "connected"

    def test_handles_connection_timeout(self) -> None:
        """Test decorator handles connection timeout errors."""

        @connection_command()
        def test_func() -> Never:
            msg = "Connection timeout occurred"
            raise CustomError(msg)

        with pytest.raises(SystemExit) as exc_info:
            test_func()
        assert exc_info.value.code == 1

    def test_connection_timeout_error_message(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test connection timeout shows appropriate error message."""

        @connection_command()
        def test_func() -> Never:
            msg = "Connection timeout"
            raise CustomError(msg)

        with pytest.raises(SystemExit):
            test_func()

        captured = capsys.readouterr()
        assert "Connection timeout" in captured.out
        assert "unreachable" in captured.out.lower()

    def test_reraises_other_exceptions(self) -> None:
        """Test decorator re-raises non-timeout exceptions."""

        @connection_command()
        def test_func() -> Never:
            msg = "Some other error"
            raise ValueError(msg)

        with pytest.raises(ValueError, match="Some other error") as exc_info:
            test_func()
        assert "Some other error" in str(exc_info.value)

"""Common decorators for CLI commands."""

import functools
import json
import click
from typing import Tuple, Type, Callable, Any
from ..utils.formatters import OutputFormatter


def handle_service_errors(*service_exceptions: Type[Exception]):
    """Decorator to handle common service exceptions with consistent error formatting.

    Args:
        service_exceptions: Tuple of exception types to catch and handle
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Extract json_output from kwargs if present
            json_output = kwargs.get("json_output", False)
            formatter = OutputFormatter(json_output)

            try:
                return func(*args, **kwargs)
            except service_exceptions as e:
                error_response = formatter.error_response(str(e))
                if json_output:
                    click.echo(error_response)
                    raise SystemExit(1)
                else:
                    click.echo(error_response, err=True)
                    raise click.ClickException(f"{func.__name__} failed")
            except Exception as e:
                # Handle unexpected errors
                error_response = formatter.error_response(f"Unexpected error: {str(e)}")
                if json_output:
                    click.echo(error_response)
                    raise SystemExit(1)
                else:
                    click.echo(error_response, err=True)
                    raise click.ClickException(f"{func.__name__} failed")

        return wrapper

    return decorator


def json_output_option(func: Callable) -> Callable:
    """Decorator to add --json-output option to a command."""
    return click.option(
        "--json-output", "-j", is_flag=True, help="Output in JSON format"
    )(func)


def validation_option(func: Callable) -> Callable:
    """Decorator to add --validate-checksum option to a command."""
    return click.option(
        "--validate-checksum", "-c", is_flag=True, help="Validate telegram checksum"
    )(func)


def common_options(func: Callable) -> Callable:
    """Decorator to add both json output and validation options."""
    func = validation_option(func)
    func = json_output_option(func)
    return func


def telegram_parser_command(service_exceptions: Tuple[Type[Exception]] = ()):
    """Decorator for telegram parsing commands with standard error handling.

    Args:
        service_exceptions: Additional service exceptions to handle
    """

    def decorator(func: Callable) -> Callable:
        # Apply common options
        func = common_options(func)

        # Apply error handling for telegram parsing
        from ...services.telegram_service import TelegramParsingError

        exceptions = (TelegramParsingError,) + service_exceptions
        func = handle_service_errors(*exceptions)(func)

        return func

    return decorator


def service_command(*service_exceptions: Type[Exception]):
    """Decorator for service-based commands with error handling and JSON output.

    Args:
        service_exceptions: Service exception types to handle
    """

    def decorator(func: Callable) -> Callable:
        func = json_output_option(func)
        func = handle_service_errors(*service_exceptions)(func)
        return func

    return decorator


def list_command(*service_exceptions: Type[Exception]):
    """Decorator for list/search commands with common options."""

    def decorator(func: Callable) -> Callable:
        func = json_output_option(func)
        func = handle_service_errors(*service_exceptions)(func)
        return func

    return decorator


def file_operation_command():
    """Decorator for file operation commands with common filters."""

    def decorator(func: Callable) -> Callable:
        func = click.option(
            "--time-range", help="Filter by time range (HH:MM:SS,mmm-HH:MM:SS,mmm)"
        )(func)
        func = click.option(
            "--filter-direction",
            type=click.Choice(["tx", "rx"]),
            help="Filter by direction",
        )(func)
        func = click.option(
            "--filter-type",
            type=click.Choice(["event", "system", "reply"]),
            help="Filter by telegram type",
        )(func)
        func = json_output_option(func)
        return func

    return decorator


def with_formatter(formatter_class=None):
    """Decorator to inject a formatter instance into the command.

    Args:
        formatter_class: Custom formatter class to use
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            json_output = kwargs.get("json_output", False)
            formatter_cls = formatter_class or OutputFormatter
            formatter = formatter_cls(json_output)
            kwargs["formatter"] = formatter
            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_arguments(*required_args: str):
    """Decorator to validate required arguments are present.

    Args:
        required_args: Names of required arguments
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            json_output = kwargs.get("json_output", False)
            formatter = OutputFormatter(json_output)

            # Check for missing required arguments
            missing_args = []
            for arg_name in required_args:
                if arg_name in kwargs and kwargs[arg_name] is None:
                    missing_args.append(arg_name)

            if missing_args:
                error_msg = f"Missing required arguments: {', '.join(missing_args)}"
                error_response = formatter.error_response(error_msg)

                if json_output:
                    click.echo(error_response)
                    raise SystemExit(1)
                else:
                    click.echo(error_response, err=True)
                    raise click.ClickException("Missing required arguments")

            return func(*args, **kwargs)

        return wrapper

    return decorator


def connection_command():
    """Decorator for commands that connect to remote services."""

    def decorator(func: Callable) -> Callable:
        func = json_output_option(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            json_output = kwargs.get("json_output", False)
            formatter = OutputFormatter(json_output)

            try:
                return func(*args, **kwargs)
            except Exception as e:
                if "Connection timeout" in str(e):
                    # Special handling for connection timeouts
                    error_msg = "Connection timeout - server may be unreachable"
                    error_response = formatter.error_response(error_msg)

                    if json_output:
                        click.echo(error_response)
                    else:
                        click.echo("Failed to connect to server", err=True)

                    raise SystemExit(1)
                else:
                    # Re-raise other exceptions to be handled by other decorators
                    raise

        return wrapper

    return decorator

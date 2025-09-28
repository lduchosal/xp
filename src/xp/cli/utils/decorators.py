"""Common decorators for CLI commands."""

import functools
from typing import Tuple, Type, Callable, Any

import click

from ..utils.formatters import OutputFormatter


def handle_service_errors(
    *service_exceptions: Type[Exception],
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to handle common service exceptions with consistent JSON error formatting.

    Args:
        service_exceptions: Tuple of exception types to catch and handle
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            formatter = OutputFormatter(True)

            try:
                return func(*args, **kwargs)
            except service_exceptions as e:
                error_response = formatter.error_response(str(e))
                click.echo(error_response)
                raise SystemExit(1)
            except Exception as e:
                # Handle unexpected errors
                error_response = formatter.error_response(f"Unexpected error: {e}")
                click.echo(error_response)
                raise SystemExit(1)

        return wrapper

    return decorator


def common_options(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to add validation option."""
    return func


def telegram_parser_command(
    service_exceptions: Tuple[Type[Exception], ...] = (),
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for telegram parsing commands with standard error handling.

    Args:
        service_exceptions: Additional service exceptions to handle
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # Apply common options
        func = common_options(func)

        # Apply error handling for telegram parsing
        from ...services.telegram_service import TelegramParsingError

        exceptions = (TelegramParsingError,) + service_exceptions
        func = handle_service_errors(*exceptions)(func)

        return func

    return decorator


def service_command(
    *service_exceptions: Type[Exception],
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for service-based commands with error handling and JSON output.

    Args:
        service_exceptions: Service exception types to handle
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        func = handle_service_errors(*service_exceptions)(func)
        return func

    return decorator


def list_command(
    *service_exceptions: Type[Exception],
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for list/search commands with common options."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        func = handle_service_errors(*service_exceptions)(func)
        return func

    return decorator


def file_operation_command() -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for file operation commands with common filters."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
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
        return func

    return decorator


def with_formatter(
    formatter_class: Any = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to inject a formatter instance into the command.

    Args:
        formatter_class: Custom formatter class to use
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            formatter_cls = formatter_class or OutputFormatter
            formatter = formatter_cls(True)
            kwargs["formatter"] = formatter
            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_arguments(
    *required_args: str,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to validate required arguments are present.

    Args:
        required_args: Names of required arguments
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            formatter = OutputFormatter(True)

            # Check for missing required arguments
            missing_args = [
                arg_name
                for arg_name in required_args
                if arg_name in kwargs and kwargs[arg_name] is None
            ]

            if missing_args:
                error_msg = f"Missing required arguments: {', '.join(missing_args)}"
                error_response = formatter.error_response(error_msg)
                click.echo(error_response)
                raise SystemExit(1)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def connection_command() -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for commands that connect to remote services."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            formatter = OutputFormatter(True)

            try:
                return func(*args, **kwargs)
            except Exception as e:
                if "Connection timeout" in str(e):
                    # Special handling for connection timeouts
                    error_msg = "Connection timeout - server may be unreachable"
                    error_response = formatter.error_response(error_msg)
                    click.echo(error_response)
                    raise SystemExit(1)
                else:
                    # Re-raise other exceptions to be handled by other decorators
                    raise

        return wrapper

    return decorator

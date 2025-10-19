"""Common decorators for CLI commands."""

import functools
from typing import Any, Callable, Tuple, Type

import click

from xp.cli.utils.formatters import OutputFormatter


def handle_service_errors(
    *service_exceptions: Type[Exception],
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Handle common service exceptions with consistent JSON error formatting.

    Args:
        service_exceptions: Tuple of exception types to catch and handle.

    Returns:
        Decorator function that wraps commands with error handling.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Apply error handling to the decorated function.

        Args:
            func: The function to decorate.

        Returns:
            Wrapped function with error handling.
        """

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Execute function with error handling.

            Args:
                args: Positional arguments passed to the decorated function.
                kwargs: Keyword arguments passed to the decorated function.

            Returns:
                Result from the decorated function.

            Raises:
                SystemExit: When a service exception or unexpected error occurs.
            """
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
    """Add validation option to command.

    Args:
        func: The function to decorate.

    Returns:
        Decorated function with common options.
    """
    return func


def telegram_parser_command(
    service_exceptions: Tuple[Type[Exception], ...] = (),
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Apply telegram parsing commands with standard error handling.

    Args:
        service_exceptions: Additional service exceptions to handle.

    Returns:
        Decorator function for telegram parsing commands.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Apply telegram parser decorators.

        Args:
            func: The function to decorate.

        Returns:
            Decorated function with telegram parsing support.
        """
        # Apply common options
        func = common_options(func)

        # Apply error handling for telegram parsing
        from xp.services.telegram.telegram_service import TelegramParsingError

        exceptions = (TelegramParsingError,) + service_exceptions
        func = handle_service_errors(*exceptions)(func)

        return func

    return decorator


def service_command(
    *service_exceptions: Type[Exception],
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Apply service-based commands with error handling and JSON output.

    Args:
        service_exceptions: Service exception types to handle.

    Returns:
        Decorator function for service commands.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Apply service command decorators.

        Args:
            func: The function to decorate.

        Returns:
            Decorated function with service error handling.
        """
        func = handle_service_errors(*service_exceptions)(func)
        return func

    return decorator


def list_command(
    *service_exceptions: Type[Exception],
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Apply list/search commands with common options.

    Args:
        service_exceptions: Service exception types to handle.

    Returns:
        Decorator function for list commands.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Apply list command decorators.

        Args:
            func: The function to decorate.

        Returns:
            Decorated function with list error handling.
        """
        func = handle_service_errors(*service_exceptions)(func)
        return func

    return decorator


def file_operation_command() -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Apply file operation commands with common filters.

    Returns:
        Decorator function for file operation commands.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Apply file operation decorators.

        Args:
            func: The function to decorate.

        Returns:
            Decorated function with filter options.
        """
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
    """Inject a formatter instance into the command.

    Args:
        formatter_class: Custom formatter class to use.

    Returns:
        Decorator function that injects a formatter.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Apply formatter injection.

        Args:
            func: The function to decorate.

        Returns:
            Wrapped function with formatter injection.
        """

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Execute function with injected formatter.

            Args:
                args: Positional arguments passed to the decorated function.
                kwargs: Keyword arguments passed to the decorated function.

            Returns:
                Result from the decorated function.
            """
            formatter_cls = formatter_class or OutputFormatter
            formatter = formatter_cls(True)
            kwargs["formatter"] = formatter
            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_arguments(
    *required_args: str,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Validate required arguments are present.

    Args:
        required_args: Names of required arguments.

    Returns:
        Decorator function that validates required arguments.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Apply argument validation.

        Args:
            func: The function to decorate.

        Returns:
            Wrapped function with argument validation.
        """

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Execute function with argument validation.

            Args:
                args: Positional arguments passed to the decorated function.
                kwargs: Keyword arguments passed to the decorated function.

            Returns:
                Result from the decorated function.

            Raises:
                SystemExit: When required arguments are missing.
            """
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
    """Apply commands that connect to remote services.

    Returns:
        Decorator function for connection commands.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Apply connection command decorators.

        Args:
            func: The function to decorate.

        Returns:
            Wrapped function with connection error handling.
        """

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Execute function with connection error handling.

            Args:
                args: Positional arguments passed to the decorated function.
                kwargs: Keyword arguments passed to the decorated function.

            Returns:
                Result from the decorated function.

            Raises:
                SystemExit: When a connection timeout occurs.
                Exception: Re-raises other exceptions for handling by other decorators.
            """
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

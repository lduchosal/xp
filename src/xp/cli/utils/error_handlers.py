"""Error handling utilities for CLI commands."""

from typing import Any, Dict, Optional

import click

from xp.cli.utils.formatters import OutputFormatter


class CLIErrorHandler:
    """Centralized error handling for CLI commands."""

    @staticmethod
    def handle_parsing_error(
        error: Exception,
        raw_input: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Handle telegram parsing errors with JSON formatting.

        Args:
            error: The parsing error that occurred.
            raw_input: The raw input that failed to parse.
            context: Additional context information.

        Raises:
            SystemExit: Always exits with code 1 after displaying error.
        """
        formatter = OutputFormatter(True)
        error_data = {"raw_input": raw_input}

        if context:
            error_data.update(context)

        error_response = formatter.error_response(str(error), error_data)
        click.echo(error_response)
        raise SystemExit(1)

    @staticmethod
    def handle_connection_error(
        error: Exception, config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Handle connection/network errors with JSON formatting.

        Args:
            error: The connection error that occurred.
            config: Configuration information (IP, port, timeout).

        Raises:
            SystemExit: Always exits with code 1 after displaying error.
        """
        formatter = OutputFormatter(True)

        if "Connection timeout" in str(error):
            if config:
                error_msg = f"Connection timeout after {config.get('timeout', 'unknown')} seconds"
                error_data = {
                    "host": config.get("ip", "unknown"),
                    "port": config.get("port", "unknown"),
                    "timeout": config.get("timeout", "unknown"),
                }
            else:
                error_msg = "Connection timeout"
                error_data = {}

            error_response = formatter.error_response(error_msg, error_data)
            click.echo(error_response)
            raise SystemExit(1)
        else:
            # Generic connection error
            error_response = formatter.error_response(str(error))
            click.echo(error_response)
            raise SystemExit(1)

    @staticmethod
    def handle_service_error(
        error: Exception, operation: str, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Handle general service errors with JSON formatting.

        Args:
            error: The service error that occurred.
            operation: Description of the operation that failed.
            context: Additional context information.

        Raises:
            SystemExit: Always exits with code 1 after displaying error.
        """
        formatter = OutputFormatter(True)
        error_data = {"operation": operation}

        if context:
            error_data.update(context)

        error_response = formatter.error_response(str(error), error_data)
        click.echo(error_response)
        raise SystemExit(1)

    @staticmethod
    def handle_validation_error(error: Exception, input_data: str) -> None:
        """Handle validation errors with JSON formatting.

        Args:
            error: The validation error that occurred.
            input_data: The input that failed validation.

        Raises:
            SystemExit: Always exits with code 1 after displaying error.
        """
        formatter = OutputFormatter(True)
        error_data = {"valid_format": False, "raw_input": input_data}

        error_response = formatter.error_response(str(error), error_data)
        click.echo(error_response)
        raise SystemExit(1)

    @staticmethod
    def handle_file_error(
        error: Exception,
        file_path: str,
        operation: str = "processing",
    ) -> None:
        """Handle file operation errors with JSON formatting.

        Args:
            error: The file error that occurred.
            file_path: Path to the file that caused the error.
            operation: Type of file operation (parsing, reading, etc.).

        Raises:
            SystemExit: Always exits with code 1 after displaying error.
        """
        formatter = OutputFormatter(True)
        error_data = {"file_path": file_path, "operation": operation}

        error_response = formatter.error_response(str(error), error_data)
        click.echo(error_response)
        raise SystemExit(1)

    @staticmethod
    def handle_not_found_error(
        error: Exception, item_type: str, identifier: str
    ) -> None:
        """Handle 'not found' errors with JSON formatting.

        Args:
            error: The not found error that occurred.
            item_type: Type of item that was not found.
            identifier: Identifier used to search for the item.

        Raises:
            SystemExit: Always exits with code 1 after displaying error.
        """
        formatter = OutputFormatter(True)
        error_data = {"item_type": item_type, "identifier": identifier}

        error_response = formatter.error_response(str(error), error_data)
        click.echo(error_response)
        raise SystemExit(1)


class ServerErrorHandler(CLIErrorHandler):
    """Specialized error handler for server operations."""

    @staticmethod
    def handle_server_startup_error(
        error: Exception, port: int, config_path: str
    ) -> None:
        """Handle server startup errors with JSON formatting.

        Args:
            error: The server startup error that occurred.
            port: Port number the server attempted to use.
            config_path: Path to the configuration file.

        Raises:
            SystemExit: Always exits with code 1 after displaying error.
        """
        formatter = OutputFormatter(True)
        error_data = {
            "port": port,
            "config": config_path,
            "operation": "server_startup",
        }

        error_response = formatter.error_response(str(error), error_data)
        click.echo(error_response)
        raise SystemExit(1)

    @staticmethod
    def handle_server_not_running_error() -> None:
        """Handle errors when server is not running with JSON formatting.

        Raises:
            SystemExit: Always exits with code 1 after displaying error.
        """
        error_response = OutputFormatter(True).error_response(
            "No server is currently running"
        )
        click.echo(error_response)
        raise SystemExit(1)

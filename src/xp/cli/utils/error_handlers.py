"""Error handling utilities for CLI commands."""

import click
from typing import Dict, Any, Optional
from .formatters import OutputFormatter


class CLIErrorHandler:
    """Centralized error handling for CLI commands."""

    @staticmethod
    def handle_parsing_error(
        error: Exception,
        json_output: bool,
        raw_input: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Handle telegram parsing errors with consistent formatting.

        Args:
            error: The parsing error that occurred
            json_output: Whether to format as JSON
            raw_input: The raw input that failed to parse
            context: Additional context information
        """
        formatter = OutputFormatter(json_output)
        error_data = {"raw_input": raw_input}

        if context:
            error_data.update(context)

        error_response = formatter.error_response(str(error), error_data)

        if json_output:
            click.echo(error_response)
            raise SystemExit(1)
        else:
            click.echo(f"Error parsing telegram: {error}", err=True)
            raise click.ClickException("Telegram parsing failed")

    @staticmethod
    def handle_connection_error(
        error: Exception, json_output: bool, config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Handle connection/network errors.

        Args:
            error: The connection error that occurred
            json_output: Whether to format as JSON
            config: Configuration information (IP, port, timeout)
        """
        formatter = OutputFormatter(json_output)

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

            if json_output:
                click.echo(error_response)
            else:
                if config:
                    click.echo(f"Connecting to {config['ip']}:{config['port']}...")
                    click.echo(
                        f"Error: Connection timeout after {config['timeout']} seconds"
                    )
                click.echo("Failed to connect to server")

            raise SystemExit(1)
        else:
            # Generic connection error
            error_response = formatter.error_response(str(error))

            if json_output:
                click.echo(error_response)
                raise SystemExit(1)
            else:
                click.echo(f"Connection error: {error}", err=True)
                raise click.ClickException("Connection failed")

    @staticmethod
    def handle_service_error(
        error: Exception,
        json_output: bool,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Handle general service errors.

        Args:
            error: The service error that occurred
            json_output: Whether to format as JSON
            operation: Description of the operation that failed
            context: Additional context information
        """
        formatter = OutputFormatter(json_output)
        error_data = {"operation": operation}

        if context:
            error_data.update(context)

        error_response = formatter.error_response(str(error), error_data)

        if json_output:
            click.echo(error_response)
            raise SystemExit(1)
        else:
            click.echo(f"Error during {operation}: {error}", err=True)
            raise click.ClickException(f"{operation.capitalize()} failed")

    @staticmethod
    def handle_validation_error(
        error: Exception, json_output: bool, input_data: str
    ) -> None:
        """Handle validation errors.

        Args:
            error: The validation error that occurred
            json_output: Whether to format as JSON
            input_data: The input that failed validation
        """
        formatter = OutputFormatter(json_output)
        error_data = {"valid_format": False, "raw_input": input_data}

        error_response = formatter.error_response(str(error), error_data)

        if json_output:
            click.echo(error_response)
            raise SystemExit(1)
        else:
            click.echo("✗ Input format is invalid", err=True)
            click.echo(f"Error: {error}", err=True)
            raise click.ClickException("Validation failed")

    @staticmethod
    def handle_file_error(
        error: Exception,
        json_output: bool,
        file_path: str,
        operation: str = "processing",
    ) -> None:
        """Handle file operation errors.

        Args:
            error: The file error that occurred
            json_output: Whether to format as JSON
            file_path: Path to the file that caused the error
            operation: Type of file operation (parsing, reading, etc.)
        """
        formatter = OutputFormatter(json_output)
        error_data = {"file_path": file_path, "operation": operation}

        error_response = formatter.error_response(str(error), error_data)

        if json_output:
            click.echo(error_response)
            raise SystemExit(1)
        else:
            click.echo(f"Error {operation} file: {error}", err=True)
            raise click.ClickException(f"File {operation} failed")

    @staticmethod
    def handle_not_found_error(
        error: Exception, json_output: bool, item_type: str, identifier: str
    ) -> None:
        """Handle 'not found' errors.

        Args:
            error: The not found error that occurred
            json_output: Whether to format as JSON
            item_type: Type of item that was not found
            identifier: Identifier used to search for the item
        """
        formatter = OutputFormatter(json_output)
        error_data = {"item_type": item_type, "identifier": identifier}

        error_response = formatter.error_response(str(error), error_data)

        if json_output:
            click.echo(error_response)
            raise SystemExit(1)
        else:
            click.echo(f"Error: {error}", err=True)
            raise click.ClickException(f"{item_type.capitalize()} lookup failed")


class ServerErrorHandler(CLIErrorHandler):
    """Specialized error handler for server operations."""

    @staticmethod
    def handle_server_startup_error(
        error: Exception, json_output: bool, port: int, config_path: str
    ) -> None:
        """Handle server startup errors."""
        formatter = OutputFormatter(json_output)
        error_data = {
            "port": port,
            "config": config_path,
            "operation": "server_startup",
        }

        error_response = formatter.error_response(str(error), error_data)

        if json_output:
            click.echo(error_response)
            raise SystemExit(1)
        else:
            click.echo(f"Error starting server: {error}", err=True)
            raise click.ClickException("Server startup failed")

    @staticmethod
    def handle_server_not_running_error(json_output: bool) -> None:
        """Handle errors when server is not running."""
        formatter = OutputFormatter(json_output)
        error_response = formatter.error_response("No server is currently running")

        if json_output:
            click.echo(error_response)
            raise SystemExit(1)
        else:
            click.echo("No server is currently running", err=True)
            raise click.ClickException("No server running")

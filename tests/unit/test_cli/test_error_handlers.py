"""Tests for CLI error handlers."""

import json

import pytest

from xp.cli.utils.error_handlers import CLIErrorHandler, ServerErrorHandler


class TestCLIErrorHandler:
    """Test CLIErrorHandler class."""

    def test_handle_parsing_error_basic(self, capsys):
        """Test basic parsing error handling."""
        with pytest.raises(SystemExit) as exc_info:
            CLIErrorHandler.handle_parsing_error(
                ValueError("Invalid format"), "<INVALID>"
            )

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["success"] is False
        assert "Invalid format" in output["error"]
        assert output["raw_input"] == "<INVALID>"

    def test_handle_parsing_error_with_context(self, capsys):
        """Test parsing error with additional context."""
        context = {"line_number": 42, "file": "test.log"}
        with pytest.raises(SystemExit) as exc_info:
            CLIErrorHandler.handle_parsing_error(
                ValueError("Parse error"), "<BAD>", context
            )

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["raw_input"] == "<BAD>"
        assert output["line_number"] == 42
        assert output["file"] == "test.log"

    def test_handle_connection_error_timeout_with_config(self, capsys):
        """Test connection timeout error with config."""
        config = {"ip": "192.168.1.1", "port": 8080, "timeout": 5}
        with pytest.raises(SystemExit) as exc_info:
            CLIErrorHandler.handle_connection_error(
                Exception("Connection timeout"), config
            )

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["success"] is False
        assert "timeout" in output["error"].lower()
        assert output["host"] == "192.168.1.1"
        assert output["port"] == 8080
        assert output["timeout"] == 5

    def test_handle_connection_error_timeout_without_config(self, capsys):
        """Test connection timeout error without config."""
        with pytest.raises(SystemExit) as exc_info:
            CLIErrorHandler.handle_connection_error(
                Exception("Connection timeout"), None
            )

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["success"] is False
        assert "Connection timeout" in output["error"]

    def test_handle_connection_error_generic(self, capsys):
        """Test generic connection error."""
        with pytest.raises(SystemExit) as exc_info:
            CLIErrorHandler.handle_connection_error(
                Exception("Network unreachable"), None
            )

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "Network unreachable" in output["error"]

    def test_handle_service_error_basic(self, capsys):
        """Test basic service error handling."""
        with pytest.raises(SystemExit) as exc_info:
            CLIErrorHandler.handle_service_error(
                RuntimeError("Service failed"), "data_processing"
            )

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["success"] is False
        assert "Service failed" in output["error"]
        assert output["operation"] == "data_processing"

    def test_handle_service_error_with_context(self, capsys):
        """Test service error with context."""
        context = {"serial_number": "12345", "retry_count": 3}
        with pytest.raises(SystemExit) as exc_info:
            CLIErrorHandler.handle_service_error(
                RuntimeError("Service unavailable"), "query", context
            )

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["operation"] == "query"
        assert output["serial_number"] == "12345"
        assert output["retry_count"] == 3

    def test_handle_validation_error(self, capsys):
        """Test validation error handling."""
        with pytest.raises(SystemExit) as exc_info:
            CLIErrorHandler.handle_validation_error(
                ValueError("Invalid checksum"), "<E14L00I02M>"
            )

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["success"] is False
        assert "Invalid checksum" in output["error"]
        assert output["valid_format"] is False
        assert output["raw_input"] == "<E14L00I02M>"

    def test_handle_file_error_default_operation(self, capsys):
        """Test file error with default operation."""
        with pytest.raises(SystemExit) as exc_info:
            CLIErrorHandler.handle_file_error(
                IOError("File not found"), "/tmp/test.log"
            )

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["success"] is False
        assert "File not found" in output["error"]
        assert output["file_path"] == "/tmp/test.log"
        assert output["operation"] == "processing"

    def test_handle_file_error_custom_operation(self, capsys):
        """Test file error with custom operation."""
        with pytest.raises(SystemExit) as exc_info:
            CLIErrorHandler.handle_file_error(
                PermissionError("Access denied"), "/tmp/test.log", "reading"
            )

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["operation"] == "reading"
        assert output["file_path"] == "/tmp/test.log"

    def test_handle_not_found_error(self, capsys):
        """Test not found error handling."""
        with pytest.raises(SystemExit) as exc_info:
            CLIErrorHandler.handle_not_found_error(
                ValueError("Module not found"), "module", "E14"
            )

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["success"] is False
        assert "Module not found" in output["error"]
        assert output["item_type"] == "module"
        assert output["identifier"] == "E14"


class TestServerErrorHandler:
    """Test ServerErrorHandler class."""

    def test_handle_server_startup_error(self, capsys):
        """Test server startup error handling."""
        with pytest.raises(SystemExit) as exc_info:
            ServerErrorHandler.handle_server_startup_error(
                RuntimeError("Port already in use"), 8080, "/config/homekit.yaml"
            )

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["success"] is False
        assert "Port already in use" in output["error"]
        assert output["port"] == 8080
        assert output["config"] == "/config/homekit.yaml"
        assert output["operation"] == "server_startup"

    def test_handle_server_not_running_error(self, capsys):
        """Test server not running error."""
        with pytest.raises(SystemExit) as exc_info:
            ServerErrorHandler.handle_server_not_running_error()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["success"] is False
        assert "No server is currently running" in output["error"]

    def test_server_error_handler_inherits_from_cli_error_handler(self):
        """Test ServerErrorHandler inherits from CLIErrorHandler."""
        assert issubclass(ServerErrorHandler, CLIErrorHandler)

    def test_server_error_handler_can_use_parent_methods(self, capsys):
        """Test ServerErrorHandler can use parent class methods."""
        with pytest.raises(SystemExit):
            ServerErrorHandler.handle_service_error(
                RuntimeError("Test error"), "test_operation"
            )

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["operation"] == "test_operation"

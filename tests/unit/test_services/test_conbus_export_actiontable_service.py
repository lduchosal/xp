# Copyright (c) 2025 ldvchosal
"""Unit tests for ConbusActiontableExportService."""

from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

from xp.models.actiontable.actiontable_type import ActionTableType
from xp.models.config.conson_module_config import (
    ConsonModuleConfig,
    ConsonModuleListConfig,
)
from xp.services.conbus.conbus_export_actiontable_service import (
    ConbusActiontableExportService,
)

SERIAL_XP24 = "0012345001"
SERIAL_XP130 = "0012345002"
TOTAL_MODULES = 2
# XP24 queues msactiontable + actiontable, XP130 queues actiontable only.
EXPECTED_QUEUE_SIZE = 3
MS_MODULE_QUEUE_SIZE = 2
SHORT_ACTIONTABLE = ["1 2 3 > 4 5 ON", "1 2 4 > 4 6 OFF"]
UPDATED_TIMEOUT_SECONDS = 5.0


def make_module(
    serial_number: str, module_type: str, link_number: int
) -> ConsonModuleConfig:
    """Build a ConsonModuleConfig for tests.

    Returns:
        A ConsonModuleConfig for tests.

    """
    return ConsonModuleConfig(
        name=f"A{link_number}",
        serial_number=serial_number,
        module_type=module_type,
        module_type_code=1,
        link_number=link_number,
    )


class TestConbusActiontableExportService:
    """Unit tests for ConbusActiontableExportService functionality."""

    @pytest.fixture
    def mock_download_service(self) -> Mock:
        """Create a mock ActionTableDownloadService.

        Returns:
            A mock ActionTableDownloadService.

        """
        mock_service = Mock()
        mock_service.on_actiontable_received = Mock()
        mock_service.on_finish = Mock()
        mock_service.on_progress = Mock()
        mock_service.on_error = Mock()
        mock_service.on_actiontable_received.connect = Mock()
        mock_service.on_finish.connect = Mock()
        mock_service.on_progress.connect = Mock()
        mock_service.on_error.connect = Mock()
        mock_service.on_actiontable_received.disconnect = Mock()
        mock_service.on_finish.disconnect = Mock()
        mock_service.on_progress.disconnect = Mock()
        mock_service.on_error.disconnect = Mock()
        mock_service.reset = Mock()
        mock_service.configure = Mock()
        mock_service.do_connect = Mock()
        mock_service.set_event_loop = Mock()
        mock_service.set_timeout = Mock()
        mock_service.start_reactor = Mock()
        mock_service.stop_reactor = Mock()
        return mock_service

    @pytest.fixture
    def module_list(self) -> ConsonModuleListConfig:
        """Create a module list with an XP24 and an XP130 module.

        Returns:
            A module list with an XP24 and an XP130 module.

        """
        return ConsonModuleListConfig(
            root=[
                make_module(SERIAL_XP24, "XP24", 1),
                make_module(SERIAL_XP130, "XP130", 2),
            ]
        )

    @pytest.fixture
    def service(
        self, mock_download_service: Mock, module_list: ConsonModuleListConfig
    ) -> ConbusActiontableExportService:
        """Create service instance with test dependencies.

        Returns:
            Service instance with test dependencies.

        """
        return ConbusActiontableExportService(
            download_service=mock_download_service,
            module_list=module_list,
        )

    def test_initialization_builds_device_queue(
        self, service: ConbusActiontableExportService
    ) -> None:
        """Test the device queue holds one entry per actiontable to download."""
        assert service.device_queue.qsize() == EXPECTED_QUEUE_SIZE
        assert service.current_module is None
        assert service.current_actiontable_type is None
        assert service.export_result.success is False
        assert service.export_status == "OK"

    @pytest.mark.parametrize(
        ("module_type", "expected_type"),
        [
            ("XP20", ActionTableType.MSACTIONTABLE_XP20),
            ("XP24", ActionTableType.MSACTIONTABLE_XP24),
            ("XP33", ActionTableType.MSACTIONTABLE_XP33),
        ],
    )
    def test_ms_actiontable_queued_first_per_module_type(
        self,
        mock_download_service: Mock,
        module_type: str,
        expected_type: ActionTableType,
    ) -> None:
        """Test XP20/XP24/XP33 modules queue their msactiontable first."""
        service = ConbusActiontableExportService(
            download_service=mock_download_service,
            module_list=ConsonModuleListConfig(
                root=[make_module(SERIAL_XP24, module_type, 1)]
            ),
        )

        assert service.device_queue.qsize() == MS_MODULE_QUEUE_SIZE
        assert service.configure() is True
        mock_download_service.configure.assert_called_once_with(
            SERIAL_XP24, expected_type
        )

    def test_configure_pops_queue_and_connects(
        self, service: ConbusActiontableExportService, mock_download_service: Mock
    ) -> None:
        """Test configure pops the next device and starts the download."""
        result = service.configure()

        assert result is True
        mock_download_service.reset.assert_called_once()
        mock_download_service.configure.assert_called_once_with(
            SERIAL_XP24, ActionTableType.MSACTIONTABLE_XP24
        )
        mock_download_service.do_connect.assert_called_once()
        assert service.current_module is not None
        assert service.current_module.serial_number == SERIAL_XP24
        assert service.current_actiontable_type == ActionTableType.MSACTIONTABLE_XP24

    def test_configure_empty_queue_returns_false(
        self, service: ConbusActiontableExportService, mock_download_service: Mock
    ) -> None:
        """Test configure returns False once the queue is drained."""
        drained = [service.configure() for _ in range(EXPECTED_QUEUE_SIZE)]

        assert drained == [True, True, True]
        assert service.configure() is False
        assert mock_download_service.do_connect.call_count == EXPECTED_QUEUE_SIZE

    def test_actiontable_received_without_type_fails(
        self, service: ConbusActiontableExportService
    ) -> None:
        """Test receiving an actiontable without configured type fails."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.on_module_actiontable_received(object(), SHORT_ACTIONTABLE)

        finish_mock.assert_called_once_with(service.export_result)
        assert service.export_result.success is False
        assert service.export_result.error == "Invalid state (current_actiontable_type)"
        assert service.export_result.export_status == "FAILED"

    def test_actiontable_received_without_module_fails(
        self, service: ConbusActiontableExportService
    ) -> None:
        """Test receiving an actiontable without a current module fails."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.current_actiontable_type = ActionTableType.ACTIONTABLE

        service.on_module_actiontable_received(object(), SHORT_ACTIONTABLE)

        finish_mock.assert_called_once_with(service.export_result)
        assert service.export_result.success is False
        assert service.export_result.error == "Invalid state (current_module)"

    @pytest.mark.parametrize(
        ("actiontable_type", "field_name"),
        [
            (ActionTableType.ACTIONTABLE, "action_table"),
            (ActionTableType.MSACTIONTABLE_XP20, "xp20_msaction_table"),
            (ActionTableType.MSACTIONTABLE_XP24, "xp24_msaction_table"),
            (ActionTableType.MSACTIONTABLE_XP33, "xp33_msaction_table"),
        ],
    )
    def test_actiontable_received_stores_table_per_type(
        self,
        service: ConbusActiontableExportService,
        module_list: ConsonModuleListConfig,
        actiontable_type: ActionTableType,
        field_name: str,
    ) -> None:
        """Test the received actiontable is stored on the matching field."""
        exported_mock = Mock()
        service.on_device_actiontable_exported.connect(exported_mock)
        module = module_list.root[0]
        service.current_module = module
        service.current_actiontable_type = actiontable_type

        service.on_module_actiontable_received(object(), SHORT_ACTIONTABLE)

        assert getattr(module, field_name) == SHORT_ACTIONTABLE
        exported_mock.assert_called_once_with(
            module, actiontable_type, SHORT_ACTIONTABLE
        )

    def test_on_module_progress_emits_current_position(
        self, service: ConbusActiontableExportService
    ) -> None:
        """Test on_module_progress reports the current module and position."""
        progress_mock = Mock()
        service.on_progress.connect(progress_mock)
        service.configure()

        service.on_module_progress()

        progress_mock.assert_called_once_with(
            SERIAL_XP24,
            ActionTableType.MSACTIONTABLE_XP24,
            TOTAL_MODULES - MS_MODULE_QUEUE_SIZE,
            TOTAL_MODULES,
        )

    def test_on_module_progress_without_module_reports_unknown(
        self, mock_download_service: Mock
    ) -> None:
        """Test on_module_progress reports UNKNOWN before configuration."""
        service = ConbusActiontableExportService(
            download_service=mock_download_service,
            module_list=ConsonModuleListConfig(root=[]),
        )
        progress_mock = Mock()
        service.on_progress.connect(progress_mock)

        service.on_module_progress()

        progress_mock.assert_called_once_with("UNKNOWN", "UNKNOWN", 0, 0)

    def test_on_module_error_fails_export(
        self, service: ConbusActiontableExportService
    ) -> None:
        """Test a module error fails the export with the error message."""
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.on_module_error("download failed")

        finish_mock.assert_called_once_with(service.export_result)
        assert service.export_result.success is False
        assert service.export_result.error == "download failed"
        assert service.export_result.export_status == "FAILED"

    def test_on_module_finish_continues_with_next_module(
        self,
        service: ConbusActiontableExportService,
        mock_download_service: Mock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test module completion saves the file and starts the next download."""
        monkeypatch.chdir(tmp_path)
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        service.configure()

        service.on_module_finish()

        # File written, next module started, export not finished yet
        assert (tmp_path / "export.yml").exists()
        assert service.export_result.output_file == "export.yml"
        finish_mock.assert_not_called()
        expected_connect_count = 2
        assert mock_download_service.do_connect.call_count == expected_connect_count

    def test_on_module_finish_last_module_succeeds(
        self,
        service: ConbusActiontableExportService,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test finishing the last module emits a successful finish."""
        monkeypatch.chdir(tmp_path)
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)
        for _ in range(EXPECTED_QUEUE_SIZE):
            service.configure()

        service.on_module_finish()

        finish_mock.assert_called_once_with(service.export_result)
        assert service.export_result.success is True
        assert service.export_result.error is None
        assert service.export_result.export_status == "OK"
        assert (tmp_path / "export.yml").exists()

    def test_save_action_table_content(
        self,
        service: ConbusActiontableExportService,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test the export file contains actiontables without internal fields."""
        monkeypatch.chdir(tmp_path)
        service.configure()
        service.on_module_actiontable_received(object(), SHORT_ACTIONTABLE)
        for _ in range(EXPECTED_QUEUE_SIZE - 1):
            service.configure()

        service.on_module_finish()

        modules = yaml.safe_load((tmp_path / "export.yml").read_text())
        assert len(modules) == TOTAL_MODULES
        assert modules[0]["serial_number"] == SERIAL_XP24
        assert modules[0]["xp24_msaction_table"] == SHORT_ACTIONTABLE
        for module in modules:
            assert "enabled" not in module
            assert "conbus_ip" not in module
            assert "conbus_port" not in module

    def test_save_failure_fails_export(
        self,
        service: ConbusActiontableExportService,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test an unwritable output file fails the export."""
        monkeypatch.chdir(tmp_path)
        # A directory named export.yml makes the file write fail
        (tmp_path / "export.yml").mkdir()
        finish_mock = Mock()
        service.on_finish.connect(finish_mock)

        service.on_module_finish()

        finish_mock.assert_called_once_with(service.export_result)
        assert service.export_result.success is False
        assert service.export_result.error is not None
        assert service.export_result.error.startswith("Failed to create export")
        assert service.export_result.export_status == "FAILED"

    def test_set_event_loop(
        self, service: ConbusActiontableExportService, mock_download_service: Mock
    ) -> None:
        """Test set_event_loop delegates to the download service."""
        event_loop = Mock()

        service.set_event_loop(event_loop)

        mock_download_service.set_event_loop.assert_called_once_with(event_loop)

    def test_set_timeout(
        self, service: ConbusActiontableExportService, mock_download_service: Mock
    ) -> None:
        """Test set_timeout delegates to the download service."""
        service.set_timeout(UPDATED_TIMEOUT_SECONDS)

        mock_download_service.set_timeout.assert_called_once_with(
            UPDATED_TIMEOUT_SECONDS
        )

    def test_start_reactor(
        self, service: ConbusActiontableExportService, mock_download_service: Mock
    ) -> None:
        """Test start_reactor delegates to the download service."""
        service.start_reactor()

        mock_download_service.start_reactor.assert_called_once()

    def test_stop_reactor(
        self, service: ConbusActiontableExportService, mock_download_service: Mock
    ) -> None:
        """Test stop_reactor delegates to the download service."""
        service.stop_reactor()

        mock_download_service.stop_reactor.assert_called_once()

    def test_context_manager_connects_and_disconnects(
        self, service: ConbusActiontableExportService, mock_download_service: Mock
    ) -> None:
        """Test context manager wires download service signals and resets state."""
        service.export_status = "FAILED"

        with service as s:
            assert s is service
            assert s.export_status == "OK"
            assert s.export_result.success is False
            mock_download_service.on_actiontable_received.connect.assert_called_once_with(
                service.on_module_actiontable_received
            )
            mock_download_service.on_finish.connect.assert_called_once_with(
                service.on_module_finish
            )
            mock_download_service.on_progress.connect.assert_called_once_with(
                service.on_module_progress
            )
            mock_download_service.on_error.connect.assert_called_once_with(
                service.on_module_error
            )

        received_signal = mock_download_service.on_actiontable_received
        received_signal.disconnect.assert_called_once_with(
            service.on_module_actiontable_received
        )
        mock_download_service.on_finish.disconnect.assert_called_once_with(
            service.on_module_finish
        )
        mock_download_service.on_progress.disconnect.assert_called_once_with(
            service.on_module_progress
        )
        mock_download_service.on_error.disconnect.assert_called_once_with(
            service.on_module_error
        )
        mock_download_service.stop_reactor.assert_called_once()

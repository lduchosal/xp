# Copyright (c) 2025 ldvchosal
"""Service for listing modules with action table configurations from conson.yml."""

import logging
from pathlib import Path
from types import TracebackType
from typing import Self

from psygnal import Signal

from xp.models.config.conson_module_config import ConsonModuleListConfig


class ActionTableListService:
    """Service for listing modules with action table configurations.

    Reads conson.yml and returns a list of all modules that have action table
    configurations defined.

    Attributes:
        on_finish: Signal emitted with dict[str, Any] when listing completes.
        on_error: Signal emitted with error message string when an error occurs.

    """

    on_finish: Signal = Signal(object)  # dict[str, Any]
    on_error: Signal = Signal(str)

    def __init__(self) -> None:
        """Initialize the action table list service."""
        self.logger = logging.getLogger(__name__)

    def __enter__(self) -> Self:
        """Context manager entry.

        Returns:
            Self for context manager use.

        """
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit."""
        # Disconnect service signals
        self.on_finish.disconnect()
        self.on_error.disconnect()

    def start(
        self,
        config_path: Path | None = None,
    ) -> None:
        """List all modules with action table configurations.

        Args:
            config_path: Optional path to conson.yml. Defaults to current directory.

        """
        # Default to current directory if not specified
        if config_path is None:
            config_path = Path.cwd() / "conson.yml"

        # Check if config file exists
        if not config_path.exists():
            self._handle_error("Error: conson.yml not found in current directory")
            return

        # Load configuration
        try:
            config = ConsonModuleListConfig.from_yaml(str(config_path))
        except Exception as e:
            self.logger.exception("Failed to load conson.yml")
            self._handle_error(f"Error: Failed to load conson.yml: {e}")
            return

        # Filter modules that have action_table configured
        modules_with_actiontable = [
            {
                "serial_number": module.serial_number,
                "module_type": module.module_type,
                "action_table": len(module.action_table) if module.action_table else 0,
                "msaction_table": (
                    1
                    if (
                        module.xp20_msaction_table
                        or module.xp24_msaction_table
                        or module.xp33_msaction_table
                    )
                    else 0
                ),
            }
            for module in config.root
        ]

        # Prepare result
        result = {"modules": modules_with_actiontable}

        # Emit finish signal
        self.on_finish.emit(result)

    def _handle_error(self, message: str) -> None:
        """Handle error and emit error signal.

        Args:
            message: Error message.

        """
        self.on_error.emit(message)

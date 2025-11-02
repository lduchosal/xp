"""Service for listing modules with action table configurations from conson.yml."""

import logging
from pathlib import Path
from typing import Any, Callable, Optional


class ActionTableListService:
    """Service for listing modules with action table configurations.

    Reads conson.yml and returns a list of all modules that have action table
    configurations defined.
    """

    def __init__(self) -> None:
        """Initialize the action table list service."""
        self.logger = logging.getLogger(__name__)
        self.finish_callback: Optional[Callable[[dict[str, Any]], None]] = None
        self.error_callback: Optional[Callable[[str], None]] = None

    def __enter__(self) -> "ActionTableListService":
        """Context manager entry.

        Returns:
            Self for context manager use.
        """
        return self

    def __exit__(self, _exc_type: Any, _exc_val: Any, _exc_tb: Any) -> None:
        """Context manager exit."""
        pass

    def start(
        self,
        finish_callback: Callable[[dict[str, Any]], None],
        error_callback: Callable[[str], None],
        config_path: Optional[Path] = None,
    ) -> None:
        """List all modules with action table configurations.

        Args:
            finish_callback: Callback to invoke with the module list.
            error_callback: Callback to invoke on error.
            config_path: Optional path to conson.yml. Defaults to current directory.
        """
        self.finish_callback = finish_callback
        self.error_callback = error_callback

        # Default to current directory if not specified
        if config_path is None:
            config_path = Path.cwd() / "conson.yml"

        # Check if config file exists
        if not config_path.exists():
            self._handle_error("Error: conson.yml not found in current directory")
            return

        # Load configuration
        try:
            from xp.models.homekit.homekit_conson_config import ConsonModuleListConfig

            config = ConsonModuleListConfig.from_yaml(str(config_path))
        except Exception as e:
            self.logger.error(f"Failed to load conson.yml: {e}")
            self._handle_error(f"Error: Failed to load conson.yml: {e}")
            return

        # Filter modules that have action_table configured
        modules_with_actiontable = [
            {
                "serial_number": module.serial_number,
                "module_type": module.module_type,
            }
            for module in config.root
        ]

        # Prepare result
        result = {"modules": modules_with_actiontable}

        # Invoke callback
        if self.finish_callback is not None:
            self.finish_callback(result)

    def _handle_error(self, message: str) -> None:
        """Handle error and invoke error callback.

        Args:
            message: Error message.
        """
        if self.error_callback is not None:
            self.error_callback(message)

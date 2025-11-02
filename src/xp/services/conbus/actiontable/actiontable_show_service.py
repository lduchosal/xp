"""Service for showing action table configuration for a specific module."""

import logging
from pathlib import Path
from typing import Any, Callable, Optional

from xp.models.homekit.homekit_conson_config import ConsonModuleConfig


class ActionTableShowService:
    """Service for showing action table configuration for a specific module.

    Reads conson.yml and returns the action table configuration for the specified
    module serial number.
    """

    def __init__(self) -> None:
        """Initialize the action table show service."""
        self.logger = logging.getLogger(__name__)
        self.finish_callback: Optional[Callable[[ConsonModuleConfig], None]] = None
        self.error_callback: Optional[Callable[[str], None]] = None

    def __enter__(self) -> "ActionTableShowService":
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
        serial_number: str,
        finish_callback: Callable[[ConsonModuleConfig], None],
        error_callback: Callable[[str], None],
        config_path: Optional[Path] = None,
    ) -> None:
        """Show action table configuration for a specific module.

        Args:
            serial_number: Module serial number.
            finish_callback: Callback to invoke with the module configuration.
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

        # Find module
        module = config.find_module(serial_number)
        if not module:
            self._handle_error(f"Error: Module {serial_number} not found in conson.yml")
            return

        # Invoke callback
        if self.finish_callback is not None:
            self.finish_callback(module)

    def _handle_error(self, message: str) -> None:
        """Handle error and invoke error callback.

        Args:
            message: Error message.
        """
        if self.error_callback is not None:
            self.error_callback(message)

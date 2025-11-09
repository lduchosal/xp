"""Conbus Event List Service for listing configured event telegrams.

This service parses action tables from conson.yml and groups events
by button configuration to show which modules are assigned to each event.
"""

import logging
from collections import defaultdict
from typing import Dict, List

from xp.models import ConbusEventListResponse
from xp.models.homekit.homekit_conson_config import ConsonModuleListConfig
from xp.services.actiontable.actiontable_serializer import ActionTableSerializer


class ConbusEventListService:
    """Service for listing configured event telegrams from action tables.

    Parses action tables from conson.yml configuration and groups modules
    by their event keys to identify common button configurations.

    Attributes:
        conson_config: Configuration containing module action tables.
        logger: Logger instance for the service.
    """

    def __init__(self, conson_config: ConsonModuleListConfig) -> None:
        """Initialize the Conbus event list service.

        Args:
            conson_config: ConsonModuleListConfig instance with module action tables.
        """
        self.conson_config = conson_config
        self.logger = logging.getLogger(__name__)

    def list_events(self) -> ConbusEventListResponse:
        """List all configured events from module action tables.

        Parses action tables, extracts event information (module_type, link, input),
        groups modules by event key, and sorts by usage count.

        Returns:
            ConbusEventListResponse with events dict mapping event keys to module names.
        """
        # Dict to track which modules are assigned to each event
        # event_key -> set of module names (using set for automatic deduplication)
        event_modules: Dict[str, set[str]] = defaultdict(set)

        # Process each module's action table
        for module in self.conson_config.root:
            # Skip modules without action table
            if not module.action_table:
                continue

            # Process each action in the module's action table
            for action in module.action_table:
                try:
                    # Use existing ActionTableSerializer to parse action
                    entry = ActionTableSerializer.parse_action_string(action)

                    # Extract event data from parsed entry
                    module_type_name = entry.module_type.name
                    link = entry.link_number
                    input_num = entry.module_input

                    # Create event key (space-separated format)
                    event_key = f"{module_type_name} {link:02d} {input_num:02d}"

                    # Add this module to the event (set automatically deduplicates)
                    event_modules[event_key].add(
                        f"{module.serial_number}:{entry.module_output}"
                    )

                except ValueError as e:
                    # Invalid action format - log warning and skip
                    self.logger.warning(
                        f"Invalid action '{action}' in module '{module.serial_number}': {e}"
                    )
                    continue

        # Convert sets to sorted lists and sort events by module count (descending)
        events_dict: Dict[str, List[str]] = {
            event_key: sorted(list(modules))
            for event_key, modules in sorted(
                event_modules.items(),
                key=lambda item: len(item[1]),
                reverse=True,
            )
        }

        return ConbusEventListResponse(events=events_dict)

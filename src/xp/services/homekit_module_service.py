import logging
from typing import Optional, List

from pydispatch import dispatcher

from xp.models.action_type import ActionType
from xp.models.homekit_conson_config import ConsonModule, HomekitModuleConfig
from xp.services.conbus_output_service import ConbusOutputService


class HomekitModuleService:

    def __init__(self, config_path: str = "conson.yml"):

        # Set up logging
        self.logger = logging.getLogger(__name__)

        self.modules_config = HomekitModuleConfig.from_yaml(config_path)
        self.output_service = ConbusOutputService()

        # Connect to PyDispatcher events
        self._setup_event_listeners()

    def get_module_by_name(self, name: str) -> Optional[ConsonModule]:
        """Get a module by its name"""
        module = next((module for module in self.modules_config.modules if module.name == name), None)
        self.logger.debug(f"Module search by name '{name}': {'found' if module else 'not found'}")
        return module

    def get_module_by_serial(self, serial_number: int) -> Optional[ConsonModule]:
        """Get a module by its serial number"""
        module = next((module for module in self.modules_config.modules if module.serial_number == serial_number), None)
        self.logger.debug(f"Module search by serial '{serial_number}': {'found' if module else 'not found'}")
        return module

    def get_modules_by_type(self, module_type: str) -> List[ConsonModule]:
        """Get all modules of a specific type"""
        modules = [module for module in self.modules_config.modules if module.module_type == module_type]
        self.logger.debug(f"Found {len(modules)} modules of type '{module_type}'")
        return modules


    def _setup_event_listeners(self):
        """Set up PyDispatcher event listeners"""
        dispatcher.connect(self._outlet_set_outlet_in_use, signal='outlet_set_outlet_in_use')
        dispatcher.connect(self._on_outlet_get_outlet_in_use, signal='outlet_get_outlet_in_use')
        dispatcher.connect(self._on_accessory_set_on, signal='accessory_set_on')
        dispatcher.connect(self._on_accessory_get_on, signal='accessory_get_on')

    def _outlet_set_outlet_in_use(self, sender, **kwargs):
        pass

    def _on_outlet_get_outlet_in_use(self, sender, **kwargs):
        pass

    def _on_accessory_set_on(self, sender, **kwargs):
        """Handle accessory set_on events from PyDispatcher"""
        serial_number: int = kwargs.get('serial_number')
        output: int = kwargs.get('output')
        value: str = kwargs.get('value')

        if not value in ["on", "off"]:
            self.logger.warning(f"Invalid value {value} (or or off)")
            return

        self.logger.info(f"Module {serial_number:010d}.{output:02d}: {value}")

        module = self.get_module_by_serial(serial_number)
        if not module:
            self.logger.warning(f"Module not found for serial {serial_number}")
            return

        action_type = ActionType.RELEASE
        if value == "on":
            action_type = ActionType.PRESS

        self.output_service.send_action(
            serial_number=f"{serial_number:010d}",
            output_number=output,
            action_type=action_type
        )

    def _on_accessory_get_on(self, sender, **kwargs):
        """Handle accessory get_on events from PyDispatcher"""
        serial_number: int = kwargs.get('serial_number')
        output: int = kwargs.get('output')

        self.logger.info(f"Module {serial_number:010d}.{output:02d}")

        module = self.get_module_by_serial(serial_number)
        if not module:
            self.logger.warning(f"Module not found for serial {serial_number}")
            return

        response = self.output_service.get_output_state(serial_number=serial_number)


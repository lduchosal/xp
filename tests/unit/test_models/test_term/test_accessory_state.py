"""Unit tests for AccessoryState model."""

from datetime import datetime

import pytest

from xp.models.term.accessory_state import AccessoryState


class TestAccessoryState:
    """Unit tests for AccessoryState dataclass."""

    @pytest.fixture
    def accessory_state(self):
        """Create a basic AccessoryState for testing."""
        return AccessoryState(
            room_name="Living Room",
            accessory_name="Main Light",
            action="a",
            output_state="ON",
            dimming_state="",
            module_name="A01",
            serial_number="1234567890",
            module_type="XP24",
            error_status="OK",
            output=1,
            sort=1,
        )

    def test_initialization(self, accessory_state):
        """Test AccessoryState initializes with correct values."""
        assert accessory_state.room_name == "Living Room"
        assert accessory_state.accessory_name == "Main Light"
        assert accessory_state.action == "a"
        assert accessory_state.output_state == "ON"
        assert accessory_state.dimming_state == ""
        assert accessory_state.module_name == "A01"
        assert accessory_state.serial_number == "1234567890"
        assert accessory_state.module_type == "XP24"
        assert accessory_state.error_status == "OK"
        assert accessory_state.output == 1
        assert accessory_state.sort == 1
        assert accessory_state.last_update is None
        assert accessory_state.toggle_action is None

    def test_initialization_with_optional_fields(self):
        """Test AccessoryState with optional fields set."""
        now = datetime.now()
        state = AccessoryState(
            room_name="Bedroom",
            accessory_name="Dimmer",
            action="b",
            output_state="ON",
            dimming_state="75%",
            module_name="A02",
            serial_number="0987654321",
            module_type="XP33LED",
            error_status="OK",
            output=2,
            sort=2,
            last_update=now,
            toggle_action="E02L01I02",
        )

        assert state.last_update == now
        assert state.toggle_action == "E02L01I02"

    def test_is_dimmable_xp33lr(self):
        """Test is_dimmable returns True for XP33LR modules."""
        state = AccessoryState(
            room_name="Room",
            accessory_name="Dimmer",
            action="a",
            output_state="ON",
            dimming_state="",
            module_name="A01",
            serial_number="1234567890",
            module_type="XP33LR",
            error_status="OK",
            output=1,
            sort=1,
        )
        assert state.is_dimmable() is True

    def test_is_dimmable_xp33led(self):
        """Test is_dimmable returns True for XP33LED modules."""
        state = AccessoryState(
            room_name="Room",
            accessory_name="LED Dimmer",
            action="a",
            output_state="ON",
            dimming_state="",
            module_name="A01",
            serial_number="1234567890",
            module_type="XP33LED",
            error_status="OK",
            output=1,
            sort=1,
        )
        assert state.is_dimmable() is True

    def test_is_dimmable_xp24(self):
        """Test is_dimmable returns False for XP24 modules."""
        state = AccessoryState(
            room_name="Room",
            accessory_name="Switch",
            action="a",
            output_state="ON",
            dimming_state="",
            module_name="A01",
            serial_number="1234567890",
            module_type="XP24",
            error_status="OK",
            output=1,
            sort=1,
        )
        assert state.is_dimmable() is False

    def test_is_dimmable_xp130(self):
        """Test is_dimmable returns False for XP130 modules."""
        state = AccessoryState(
            room_name="Room",
            accessory_name="Sensor",
            action="a",
            output_state="?",
            dimming_state="",
            module_name="A01",
            serial_number="1234567890",
            module_type="XP130",
            error_status="OK",
            output=1,
            sort=1,
        )
        assert state.is_dimmable() is False

    def test_output_states(self):
        """Test various output state values."""
        for output_state in ("ON", "OFF", "?"):
            state = AccessoryState(
                room_name="Room",
                accessory_name="Light",
                action="a",
                output_state=output_state,
                dimming_state="",
                module_name="A01",
                serial_number="1234567890",
                module_type="XP24",
                error_status="OK",
                output=1,
                sort=1,
            )
            assert state.output_state == output_state

    def test_error_status_values(self):
        """Test various error status values."""
        for error_status in ("OK", "E10", "E15"):
            state = AccessoryState(
                room_name="Room",
                accessory_name="Light",
                action="a",
                output_state="ON",
                dimming_state="",
                module_name="A01",
                serial_number="1234567890",
                module_type="XP24",
                error_status=error_status,
                output=1,
                sort=1,
            )
            assert state.error_status == error_status

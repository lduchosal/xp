"""Unit tests for event telegram models."""

from datetime import datetime

import pytest

from xp.models import EventType, InputType
from xp.models.telegram.event_telegram import EventTelegram


class TestEventTelegram:
    """Test cases for EventTelegram model."""

    def test_button_press_telegram(self):
        """Test parsing a button press telegram."""
        telegram = EventTelegram(
            module_type=14,
            link_number=0,
            input_number=2,
            event_type=EventType.BUTTON_PRESS,
            checksum="AK",
            raw_telegram="<E14L00I02MAK>",
        )

        assert telegram.module_type == 14
        assert telegram.link_number == 0
        assert telegram.input_number == 2
        assert telegram.event_type == EventType.BUTTON_PRESS
        assert telegram.checksum == "AK"
        assert telegram.raw_telegram == "<E14L00I02MAK>"
        assert telegram.is_button_press is True
        assert telegram.is_button_release is False
        assert telegram.input_type == InputType.PUSH_BUTTON

    def test_button_release_telegram(self):
        """Test parsing a button release telegram."""
        telegram = EventTelegram(
            module_type=14,
            link_number=1,
            input_number=3,
            event_type=EventType.BUTTON_RELEASE,
            checksum="B1",
            raw_telegram="<E14L01I03BB1>",
        )

        assert telegram.event_type == EventType.BUTTON_RELEASE
        assert telegram.is_button_press is False
        assert telegram.is_button_release is True

    def test_ir_remote_input_type(self):
        """Test IR remote input type classification."""
        telegram = EventTelegram(
            module_type=14,
            link_number=0,
            input_number=25,  # IR remote range 10-89
            event_type=EventType.BUTTON_PRESS,
            checksum="XX",
            raw_telegram="<E14L00I25MXX>",
        )

        assert telegram.input_type == InputType.IR_REMOTE

    def test_proximity_sensor_input_type(self):
        """Test proximity sensor input type classification."""
        telegram = EventTelegram(
            module_type=14,
            link_number=0,
            input_number=90,  # Proximity sensor
            event_type=EventType.BUTTON_PRESS,
            checksum="XX",
            raw_telegram="<E14L00I90MXX>",
        )

        assert telegram.input_type == InputType.PROXIMITY_SENSOR

    def test_invalid_output_number_raises_error(self):
        """Test that invalid input numbers raise ValueError."""
        telegram = EventTelegram(
            module_type=14,
            link_number=0,
            input_number=95,  # Invalid input number
            event_type=EventType.BUTTON_PRESS,
            checksum="XX",
            raw_telegram="<E14L00I95MXX>",
        )

        with pytest.raises(ValueError, match="Invalid input number: 95"):
            _ = telegram.input_type

    def test_to_dict(self):
        """Test dictionary serialization."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        result = EventTelegram(
            module_type=14,
            link_number=0,
            input_number=2,
            event_type=EventType.BUTTON_PRESS,
            checksum="AK",
            raw_telegram="<E14L00I02MAK>",
            timestamp=timestamp,
        ).to_dict()

        # Updated to include module_info and checksum_validated
        expected = {
            "module_type": 14,
            "link_number": 0,
            "output_number": 2,
            "event_type": "M",
            "event_type_name": "button_press",
            "input_type": "push_button",
            "checksum": "AK",
            "checksum_validated": None,
            "raw_telegram": "<E14L00I02MAK>",
            "telegram_type": "E",
            "timestamp": "2023-01-01T12:00:00",
            "module_info": {
                "name": "XP2606",
                "description": "5 way push button panel with sesam, L-Team design",
                "category": "Interface Panels",
            },
        }
        assert result == expected

    def test_str_representation(self):
        """Test human-readable string representation."""
        telegram = EventTelegram(
            module_type=14,
            link_number=0,
            input_number=2,
            event_type=EventType.BUTTON_PRESS,
            checksum="AK",
            raw_telegram="<E14L00I02MAK>",
        )

        # Updated to include module name
        expected = "XP2606 (Type 14) Link 00 Input 02 (push_button) pressed"
        assert str(telegram) == expected

    def test_timestamp_auto_generation(self):
        """Test that timestamp is auto-generated if not provided."""
        before = datetime.now()
        telegram = EventTelegram(
            module_type=14,
            link_number=0,
            input_number=2,
            event_type=EventType.BUTTON_PRESS,
            checksum="AK",
            raw_telegram="<E14L00I02MAK>",
        )
        after = datetime.now()

        assert telegram.timestamp is not None
        assert before <= telegram.timestamp <= after

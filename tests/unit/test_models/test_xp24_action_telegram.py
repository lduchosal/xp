"""Unit tests for XP24ActionTelegram model."""

from datetime import datetime
from unittest.mock import patch

from xp.models.input_telegram import InputTelegram
from xp.models.action_type import ActionType


class TestActionType:
    """Test cases for ActionType enum."""

    def test_action_type_values(self):
        """Test ActionType enum values."""
        assert ActionType.PRESS.value == "AA"
        assert ActionType.RELEASE.value == "AB"

    def test_from_code_valid(self):
        """Test ActionType.from_code with valid codes."""
        assert ActionType.from_code("AA") == ActionType.PRESS
        assert ActionType.from_code("AB") == ActionType.RELEASE

    def test_from_code_invalid(self):
        """Test ActionType.from_code with invalid codes."""
        assert ActionType.from_code("XX") is None
        assert ActionType.from_code("") is None


class TestXP24ActionTelegram:
    """Test cases for XP24ActionTelegram model."""

    def test_init_default_values(self):
        """Test XP24ActionTelegram initialization with default values."""
        telegram = InputTelegram(checksum="FN", raw_telegram="<S0020044964F27D00AAFN>")

        assert telegram.serial_number == ""
        assert telegram.input_number == 0
        assert telegram.action_type is None
        assert telegram.checksum == "FN"
        assert telegram.raw_telegram == "<S0020044964F27D00AAFN>"
        assert telegram.checksum_validated is None
        assert telegram.timestamp is not None

    def test_init_with_values(self):
        """Test XP24ActionTelegram initialization with specific values."""
        test_time = datetime(2023, 1, 1, 12, 0, 0)

        telegram = InputTelegram(
            serial_number="0020044964",
            input_number=2,
            action_type=ActionType.PRESS,
            checksum="FN",
            raw_telegram="<S0020044964F27D02AAFN>",
            checksum_validated=True,
            timestamp=test_time,
        )

        assert telegram.serial_number == "0020044964"
        assert telegram.input_number == 2
        assert telegram.action_type == ActionType.PRESS
        assert telegram.checksum == "FN"
        assert telegram.raw_telegram == "<S0020044964F27D02AAFN>"
        assert telegram.checksum_validated is True
        assert telegram.timestamp == test_time

    @patch("xp.models.input_telegram.datetime")
    def test_post_init_sets_timestamp(self, mock_datetime):
        """Test that __post_init__ sets timestamp when None."""
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        telegram = InputTelegram(checksum="FN", raw_telegram="<S0020044964F27D00AAFN>")

        assert telegram.timestamp == mock_now
        mock_datetime.now.assert_called_once()

    def test_post_init_preserves_existing_timestamp(self):
        """Test that __post_init__ preserves existing timestamp."""
        existing_time = datetime(2023, 1, 1, 12, 0, 0)

        telegram = InputTelegram(
            checksum="FN",
            raw_telegram="<S0020044964F27D00AAFN>",
            timestamp=existing_time,
        )

        assert telegram.timestamp == existing_time

    def test_action_description_press(self):
        """Test action_description property for PRESS action."""
        telegram = InputTelegram(
            action_type=ActionType.PRESS,
            checksum="FN",
            raw_telegram="<S0020044964F27D00AAFN>",
        )

        assert telegram.action_description == "Press (Make)"

    def test_action_description_release(self):
        """Test action_description property for RELEASE action."""
        telegram = InputTelegram(
            action_type=ActionType.RELEASE,
            checksum="FN",
            raw_telegram="<S0020044964F27D00ABFN>",
        )

        assert telegram.action_description == "Release (Break)"

    def test_action_description_none(self):
        """Test action_description property when action_type is None."""
        telegram = InputTelegram(
            action_type=None, checksum="FN", raw_telegram="<S0020044964F27D00AAFN>"
        )

        assert telegram.action_description == "Unknown Action"

    def test_input_description(self):
        """Test input_description property."""
        telegram = InputTelegram(
            input_number=2, checksum="FN", raw_telegram="<S0020044964F27D02AAFN>"
        )

        assert telegram.input_description == "Input 2"

    def test_to_dict_complete(self):
        """Test to_dict method with complete data."""
        test_time = datetime(2023, 1, 1, 12, 0, 0)

        telegram = InputTelegram(
            serial_number="0020044964",
            input_number=1,
            action_type=ActionType.PRESS,
            checksum="FN",
            raw_telegram="<S0020044964F27D01AAFN>",
            checksum_validated=True,
            timestamp=test_time,
        )

        expected = {
            "serial_number": "0020044964",
            "input_number": 1,
            "input_description": "Input 1",
            "action_type": {"code": "AA", "description": "Press (Make)"},
            "checksum": "FN",
            "checksum_validated": True,
            "raw_telegram": "<S0020044964F27D01AAFN>",
            "timestamp": "2023-01-01T12:00:00",
            "telegram_type": "xp_input",
        }

        assert telegram.to_dict() == expected

    def test_to_dict_minimal(self):
        """Test to_dict method with minimal data."""
        telegram = InputTelegram(
            action_type=None,
            checksum="FN",
            raw_telegram="<S0020044964F27D00AAFN>",
            timestamp=None,
        )

        result = telegram.to_dict()

        assert result["serial_number"] == ""
        assert result["input_number"] == 0
        assert result["action_type"]["code"] is None
        assert result["action_type"]["description"] == "Unknown Action"
        assert result["timestamp"] is not None  # __post_init__ sets it
        assert result["telegram_type"] == "xp_input"

    def test_str_representation(self):
        """Test __str__ method."""
        telegram = InputTelegram(
            serial_number="0020044964",
            input_number=3,
            action_type=ActionType.RELEASE,
            checksum="FN",
            raw_telegram="<S0020044964F27D03ABFN>",
        )

        expected = "XP Input: Release (Break) on Input 3 for device 0020044964"
        assert str(telegram) == expected

    def test_str_representation_unknown_action(self):
        """Test __str__ method with unknown action."""
        telegram = InputTelegram(
            serial_number="0020044964",
            input_number=0,
            action_type=None,
            checksum="FN",
            raw_telegram="<S0020044964F27D00AAFN>",
        )

        expected = "XP Input: Unknown Action on Input 0 for device 0020044964"
        assert str(telegram) == expected

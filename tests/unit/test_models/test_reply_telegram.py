"""Unit tests for ReplyTelegram model.

Tests the reply telegram model functionality including parsing,
value interpretation, and data structure integrity.
"""

from datetime import datetime

import pytest

from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction


class TestReplyTelegram:
    """Test ReplyTelegram model."""

    def test_reply_telegram_ack(self):
        """Test basic reply telegram creation."""
        telegram = ReplyTelegram(
            serial_number="0012345003",
            system_function=SystemFunction.ACK,
            datapoint_type=None,
            data_value="",
            checksum="FF",
            raw_telegram="<R0012345003F18DFF>",
        )

        assert telegram.serial_number == "0012345003"
        assert telegram.system_function == SystemFunction.ACK
        assert telegram.datapoint_type is None
        assert telegram.checksum == "FF"
        assert telegram.raw_telegram == "<R0012345003F18DFF>"
        assert telegram.timestamp is not None
        assert isinstance(telegram.timestamp, datetime)

    def test_reply_telegram_creation(self):
        """Test basic reply telegram creation."""
        telegram = ReplyTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            data_value="+26,0§C",
            checksum="IL",
            raw_telegram="<R0020012521F02D18+26,0§CIL>",
        )

        assert telegram.serial_number == "0020012521"
        assert telegram.system_function == SystemFunction.READ_DATAPOINT
        assert telegram.datapoint_type == DataPointType.TEMPERATURE
        assert telegram.data_value == "+26,0§C"
        assert telegram.checksum == "IL"
        assert telegram.raw_telegram == "<R0020012521F02D18+26,0§CIL>"
        assert telegram.timestamp is not None
        assert isinstance(telegram.timestamp, datetime)

    def test_reply_telegram_with_timestamp(self):
        """Test reply telegram creation with explicit timestamp."""
        test_time = datetime(2023, 1, 1, 12, 0, 0)
        telegram = ReplyTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            data_value="+26,0§C",
            checksum="IL",
            raw_telegram="<R0020012521F02D18+26,0§CIL>",
            timestamp=test_time,
        )

        assert telegram.timestamp == test_time

    def test_function_description(self):
        """Test function description property."""
        telegram = ReplyTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            data_value="+26,0§C",
            checksum="IL",
            raw_telegram="<R0020012521F02D18+26,0§CIL>",
        )

        assert telegram.system_function is not None
        assert telegram.system_function.name == "READ_DATAPOINT"

        # Test other functions
        telegram.system_function = SystemFunction.WRITE_CONFIG
        assert telegram.system_function.name == "WRITE_CONFIG"

        telegram.system_function = SystemFunction.READ_CONFIG
        assert telegram.system_function.name == "READ_CONFIG"

    def test_data_point_description(self):
        """Test data point description property."""
        telegram = ReplyTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            data_value="+26,0§C",
            checksum="IL",
            raw_telegram="<R0020012521F02D18+26,0§CIL>",
        )

        assert telegram.datapoint_type is not None
        assert telegram.datapoint_type.name == "TEMPERATURE"

        # Test other data points
        telegram.datapoint_type = DataPointType.SW_TOP_VERSION
        assert telegram.datapoint_type.name == "SW_TOP_VERSION"

        telegram.datapoint_type = DataPointType.VOLTAGE
        assert telegram.datapoint_type.name == "VOLTAGE"

    def test_parse_temperature_value(self):
        """Test temperature value parsing."""
        telegram = ReplyTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            data_value="+26,0§C",
            checksum="IL",
            raw_telegram="<R0020012521F02D18+26,0§CIL>",
        )

        parsed = telegram.parse_datapoint_value

        assert parsed["parsed"] is True
        assert parsed["value"] == 26.0
        assert parsed["unit"] == "°C"
        assert parsed["formatted"] == "26.0°C"
        assert parsed["raw_value"] == "+26,0§C"

    def test_parse_temperature_negative(self):
        """Test negative temperature value parsing."""
        telegram = ReplyTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            data_value="-15,5§C",
            checksum="AB",
            raw_telegram="<R0020012521F02D18-15,5§CAB>",
        )

        parsed = telegram.parse_datapoint_value

        assert parsed["parsed"] is True
        assert parsed["value"] == -15.5
        assert parsed["unit"] == "°C"
        assert parsed["formatted"] == "-15.5°C"

    def test_parse_humidity_value(self):
        """Test humidity value parsing."""
        telegram = ReplyTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.SW_TOP_VERSION,
            data_value="+65,5§RH",
            checksum="XY",
            raw_telegram="<R0020012521F02D19+65,5§RHXY>",
        )

        parsed = telegram.parse_datapoint_value

        assert parsed["parsed"] is True
        assert parsed["value"] == 65.5
        assert parsed["unit"] == "%RH"
        assert parsed["formatted"] == "65.5%RH"
        assert parsed["raw_value"] == "+65,5§RH"

    def test_parse_voltage_value(self):
        """Test voltage value parsing."""
        telegram = ReplyTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.VOLTAGE,
            data_value="+12,5§V",
            checksum="VW",
            raw_telegram="<R0020012521F02D20+12,5§VVW>",
        )

        parsed = telegram.parse_datapoint_value

        assert parsed["parsed"] is True
        assert parsed["value"] == 12.5
        assert parsed["unit"] == "V"
        assert parsed["formatted"] == "12.5V"
        assert parsed["raw_value"] == "+12,5§V"

    def test_parse_current_value(self):
        """Test current value parsing."""
        telegram = ReplyTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_ENERGY_LEVEL,
            data_value="+0,25§A",
            checksum="CD",
            raw_telegram="<R0020012521F02D21+0,25§ACD>",
        )

        parsed = telegram.parse_datapoint_value

        assert parsed["parsed"] is True
        assert parsed["value"] == 0.25
        assert parsed["unit"] == "A"
        assert parsed["formatted"] == "0.25A"
        assert parsed["raw_value"] == "+0,25§A"

    def test_parse_invalid_temperature(self):
        """Test parsing invalid temperature value."""
        telegram = ReplyTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            data_value="invalid§C",
            checksum="ER",
            raw_telegram="<R0020012521F02D18invalid§CER>",
        )

        parsed = telegram.parse_datapoint_value

        assert parsed["parsed"] is False
        assert "error" in parsed
        assert parsed["raw_value"] == "invalid§C"

    def test_parse_malformed_temperature(self):
        """Test parsing malformed temperature value."""
        telegram = ReplyTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            data_value="nounit",
            checksum="ER",
            raw_telegram="<R0020012521F02D18nounitER>",
        )

        parsed = telegram.parse_datapoint_value

        assert parsed["parsed"] is False
        assert parsed["raw_value"] == "nounit"

    def test_to_dict(self):
        """Test to_dict method."""
        result = ReplyTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            data_value="+26,0§C",
            checksum="IL",
            raw_telegram="<R0020012521F02D18+26,0§CIL>",
        ).to_dict()

        assert isinstance(result, dict)
        assert result["serial_number"] == "0020012521"
        assert result["system_function"]["code"] == "02"
        assert result["system_function"]["description"] == "READ_DATAPOINT"
        assert result["datapoint_type"]["code"] == "18"
        assert result["datapoint_type"]["description"] == "TEMPERATURE"
        assert result["data_value"]["raw"] == "+26,0§C"
        assert result["data_value"]["parsed"]["parsed"] is True
        assert result["data_value"]["parsed"]["value"] == 26.0
        assert result["checksum"] == "IL"
        assert result["raw_telegram"] == "<R0020012521F02D18+26,0§CIL>"
        assert result["telegram_type"] == "R"
        assert "timestamp" in result

    def test_str_representation(self):
        """Test string representation."""
        telegram = ReplyTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            data_value="+26,0§C",
            checksum="IL",
            raw_telegram="<R0020012521F02D18+26,0§CIL>",
        )

        str_repr = str(telegram)

        assert "Reply Telegram" in str_repr
        assert "READ_DATAPOINT" in str_repr
        assert "TEMPERATURE" in str_repr
        assert "26.0°C" in str_repr
        assert "0020012521" in str_repr

    def test_str_representation_unparsed_value(self):
        """Test string representation with unparsed value."""
        telegram = ReplyTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_TYPE,
            data_value="CUSTOM_STATUS",
            checksum="CS",
            raw_telegram="<R0020012521F02D00CUSTOM_STATUSCS>",
        )

        str_repr = str(telegram)

        assert "Reply Telegram" in str_repr
        assert "CUSTOM_STATUS" in str_repr

    @pytest.mark.parametrize(
        "data_value,expected_value,expected_unit",
        [
            ("+26,0§C", 26.0, "°C"),
            ("-10,5§C", -10.5, "°C"),
            ("+0,0§C", 0.0, "°C"),
            ("+100,1§C", 100.1, "°C"),
        ],
    )
    def test_temperature_parsing_variations(
        self, data_value, expected_value, expected_unit
    ):
        """Test temperature parsing with various values."""
        telegram = ReplyTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            data_value=data_value,
            checksum="AB",
            raw_telegram=f"<R0020012521F02D18{data_value}AB>",
        )

        parsed = telegram.parse_datapoint_value

        assert parsed["parsed"] is True
        assert parsed["value"] == expected_value
        assert parsed["unit"] == expected_unit

    @pytest.mark.parametrize(
        "data_value,expected_value",
        [
            ("+65,5§RH", 65.5),
            ("+0,0§RH", 0.0),
            ("+100,0§RH", 100.0),
            ("+50,3§RH", 50.3),
        ],
    )
    def test_humidity_parsing_variations(self, data_value, expected_value):
        """Test humidity parsing with various values."""
        telegram = ReplyTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.SW_TOP_VERSION,
            data_value=data_value,
            checksum="AB",
            raw_telegram=f"<R0020012521F02D19{data_value}AB>",
        )

        parsed = telegram.parse_datapoint_value

        assert parsed["parsed"] is True
        assert parsed["value"] == expected_value
        assert parsed["unit"] == "%RH"

    @pytest.mark.parametrize(
        "data_value,expected_value",
        [("+12,5§V", 12.5), ("+0,0§V", 0.0), ("+230,0§V", 230.0), ("+3,3§V", 3.3)],
    )
    def test_voltage_parsing_variations(self, data_value, expected_value):
        """Test voltage parsing with various values."""
        telegram = ReplyTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.VOLTAGE,
            data_value=data_value,
            checksum="AB",
            raw_telegram=f"<R0020012521F02D20{data_value}AB>",
        )

        parsed = telegram.parse_datapoint_value

        assert parsed["parsed"] is True
        assert parsed["value"] == expected_value
        assert parsed["unit"] == "V"

    @pytest.mark.parametrize(
        "data_value,expected_value",
        [("+0,25§A", 0.25), ("+0,00§A", 0.0), ("+1,50§A", 1.5), ("+10,00§A", 10.0)],
    )
    def test_current_parsing_variations(self, data_value, expected_value):
        """Test current parsing with various values."""
        telegram = ReplyTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_ENERGY_LEVEL,
            data_value=data_value,
            checksum="AB",
            raw_telegram=f"<R0020012521F02D21{data_value}AB>",
        )

        parsed = telegram.parse_datapoint_value

        assert parsed["parsed"] is True
        assert parsed["value"] == expected_value
        assert parsed["unit"] == "A"

    def test_telegram_equality(self):
        """Test telegram object equality."""
        timestamp = datetime.now()

        telegram1 = ReplyTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            data_value="+26,0§C",
            checksum="IL",
            raw_telegram="<R0020012521F02D18+26,0§CIL>",
            timestamp=timestamp,
        )

        telegram2 = ReplyTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            data_value="+26,0§C",
            checksum="IL",
            raw_telegram="<R0020012521F02D18+26,0§CIL>",
            timestamp=timestamp,
        )

        # Dataclass should provide equality
        assert telegram1 == telegram2

    def test_post_init_timestamp_generation(self):
        """Test that __post_init__ sets timestamp if not provided."""
        before = datetime.now()

        telegram = ReplyTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            data_value="+26,0§C",
            checksum="IL",
            raw_telegram="<R0020012521F02D18+26,0§CIL>",
        )

        after = datetime.now()

        assert telegram.timestamp is not None
        assert before <= telegram.timestamp <= after

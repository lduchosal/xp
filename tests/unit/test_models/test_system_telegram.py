"""Unit tests for SystemTelegram model.

Tests the system telegram model functionality including parsing,
validation, and data structure integrity.
"""

from datetime import datetime

import pytest

from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram


class TestSystemFunction:
    """Test SystemFunction enum."""

    def test_from_code_valid(self):
        """Test from_code with valid codes."""
        assert SystemFunction.from_code("01") == SystemFunction.DISCOVERY
        assert SystemFunction.from_code("02") == SystemFunction.READ_DATAPOINT
        assert SystemFunction.from_code("03") == SystemFunction.READ_CONFIG
        assert SystemFunction.from_code("04") == SystemFunction.WRITE_CONFIG
        assert SystemFunction.from_code("05") == SystemFunction.BLINK
        assert SystemFunction.from_code("06") == SystemFunction.UNBLINK

    def test_from_code_invalid(self):
        """Test from_code with invalid codes."""
        assert SystemFunction.from_code("99") is None
        assert SystemFunction.from_code("XX") is None
        assert SystemFunction.from_code("") is None

    def test_enum_values(self):
        """Test enum values are correct."""
        assert SystemFunction.DISCOVERY.value == "01"
        assert SystemFunction.READ_DATAPOINT.value == "02"
        assert SystemFunction.READ_CONFIG.value == "03"
        assert SystemFunction.WRITE_CONFIG.value == "04"
        assert SystemFunction.BLINK.value == "05"
        assert SystemFunction.UNBLINK.value == "06"


class TestDataPointType:
    """Test DataPointType enum."""

    def test_from_code_valid(self):
        """Test from_code with valid codes."""
        assert DataPointType.from_code("18") == DataPointType.TEMPERATURE
        assert DataPointType.from_code("19") == DataPointType.SW_TOP_VERSION
        assert DataPointType.from_code("20") == DataPointType.VOLTAGE
        assert DataPointType.from_code("17") == DataPointType.MODULE_ENERGY_LEVEL
        assert DataPointType.from_code("00") == DataPointType.MODULE_TYPE
        assert DataPointType.from_code("02") == DataPointType.SW_VERSION
        assert DataPointType.from_code("04") == DataPointType.LINK_NUMBER
        assert DataPointType.from_code("07") == DataPointType.MODULE_TYPE_CODE
        assert DataPointType.from_code("10") == DataPointType.MODULE_ERROR_CODE
        assert DataPointType.from_code("12") == DataPointType.MODULE_OUTPUT_STATE
        assert DataPointType.from_code("13") == DataPointType.MODULE_FW_CRC
        assert DataPointType.from_code("14") == DataPointType.MODULE_ACTION_TABLE_CRC
        assert DataPointType.from_code("15") == DataPointType.MODULE_LIGHT_LEVEL

    def test_from_code_invalid(self):
        """Test from_code with invalid codes."""
        assert DataPointType.from_code("99") is None
        assert DataPointType.from_code("XX") is None
        assert DataPointType.from_code("") is None

    def test_enum_values(self):
        """Test enum values are correct."""
        assert DataPointType.TEMPERATURE.value == "18"
        assert DataPointType.SW_TOP_VERSION.value == "19"
        assert DataPointType.VOLTAGE.value == "20"
        assert DataPointType.MODULE_ENERGY_LEVEL.value == "17"
        assert DataPointType.MODULE_TYPE.value == "00"
        assert DataPointType.SW_VERSION.value == "02"
        assert DataPointType.LINK_NUMBER.value == "04"
        assert DataPointType.MODULE_TYPE_CODE.value == "07"
        assert DataPointType.MODULE_ERROR_CODE.value == "10"
        assert DataPointType.MODULE_OUTPUT_STATE.value == "12"
        assert DataPointType.MODULE_FW_CRC.value == "13"
        assert DataPointType.MODULE_ACTION_TABLE_CRC.value == "14"
        assert DataPointType.MODULE_LIGHT_LEVEL.value == "15"
        assert DataPointType.LINK_NUMBER.value == "04"  # Legacy alias


class TestSystemTelegram:
    """Test SystemTelegram model."""

    def test_system_telegram_creation(self):
        """Test basic system telegram creation."""
        telegram = SystemTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>",
        )

        assert telegram.serial_number == "0020012521"
        assert telegram.system_function == SystemFunction.READ_DATAPOINT
        assert telegram.datapoint_type == DataPointType.TEMPERATURE
        assert telegram.checksum == "FN"
        assert telegram.raw_telegram == "<S0020012521F02D18FN>"
        assert telegram.timestamp is not None
        assert isinstance(telegram.timestamp, datetime)

    def test_system_telegram_with_timestamp(self):
        """Test system telegram creation with explicit timestamp."""
        test_time = datetime(2023, 1, 1, 12, 0, 0)
        telegram = SystemTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>",
            timestamp=test_time,
        )

        assert telegram.timestamp == test_time

    def test_function_description(self):
        """Test function description property."""
        telegram = SystemTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>",
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
        telegram = SystemTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>",
        )

        assert telegram.datapoint_type is not None
        assert telegram.datapoint_type.name == "TEMPERATURE"

        # Test other data points
        telegram.datapoint_type = DataPointType.SW_TOP_VERSION
        assert telegram.datapoint_type.name == "SW_TOP_VERSION"

        telegram.datapoint_type = DataPointType.VOLTAGE
        assert telegram.datapoint_type.name == "VOLTAGE"

        telegram.datapoint_type = DataPointType.MODULE_ENERGY_LEVEL
        assert telegram.datapoint_type.name == "MODULE_ENERGY_LEVEL"

        telegram.datapoint_type = DataPointType.MODULE_TYPE
        assert telegram.datapoint_type.name == "MODULE_TYPE"

    def test_to_dict(self):
        """Test to_dict method."""
        result = SystemTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>",
        ).to_dict()

        assert isinstance(result, dict)
        assert result["serial_number"] == "0020012521"
        assert result["system_function"]["code"] == "02"
        assert result["system_function"]["description"] == "READ_DATAPOINT"
        assert result["datapoint_type"]["code"] == "18"
        assert result["datapoint_type"]["description"] == "TEMPERATURE"
        assert result["checksum"] == "FN"
        assert result["raw_telegram"] == "<S0020012521F02D18FN>"
        assert result["telegram_type"] == "S"
        assert "timestamp" in result
        assert result["timestamp"] is not None

    def test_str_representation(self):
        """Test string representation."""
        telegram = SystemTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>",
        )

        str_repr = str(telegram)

        assert "System Telegram" in str_repr
        assert "READ_DATAPOINT" in str_repr
        assert "with data TEMPERATURE" in str_repr
        assert "from device 0020012521" in str_repr

    @pytest.mark.parametrize(
        "function,description",
        [
            (SystemFunction.DISCOVERY, "DISCOVERY"),
            (SystemFunction.READ_DATAPOINT, "READ_DATAPOINT"),
            (SystemFunction.READ_CONFIG, "READ_CONFIG"),
            (SystemFunction.WRITE_CONFIG, "WRITE_CONFIG"),
            (SystemFunction.BLINK, "BLINK"),
            (SystemFunction.UNBLINK, "UNBLINK"),
        ],
    )
    def test_function_descriptions(self, function, description):
        """Test all function descriptions."""
        telegram = SystemTelegram(
            serial_number="0020012521",
            system_function=function,
            datapoint_type=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>",
        )

        assert telegram.system_function is not None
        assert telegram.system_function.name == description

    def test_telegram_equality(self):
        """Test telegram object equality."""
        timestamp = datetime.now()

        telegram1 = SystemTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>",
            timestamp=timestamp,
        )

        telegram2 = SystemTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>",
            timestamp=timestamp,
        )

        # Dataclass should provide equality
        assert telegram1 == telegram2

    def test_telegram_with_different_serial_numbers(self):
        """Test telegrams with different serial numbers."""
        telegram1 = SystemTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>",
        )

        telegram2 = SystemTelegram(
            serial_number="1234567890",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            checksum="AB",
            raw_telegram="<S1234567890F02D18AB>",
        )

        assert telegram1.serial_number != telegram2.serial_number
        assert telegram1.checksum != telegram2.checksum
        assert telegram1.raw_telegram != telegram2.raw_telegram

    def test_post_init_timestamp_generation(self):
        """Test that __post_init__ sets timestamp if not provided."""
        before = datetime.now()

        telegram = SystemTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>",
        )

        after = datetime.now()

        assert telegram.timestamp is not None
        assert before <= telegram.timestamp <= after

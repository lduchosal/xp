"""Tests for SystemTelegram enhancements for link number functionality."""

from datetime import datetime

from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram


class TestSystemTelegramEnhancements:
    """Test enhancements to SystemTelegram for link number support."""

    def test_system_function_ack_nak(self):
        """Test ACK and NAK system functions."""
        # Test ACK
        ack_function = SystemFunction.from_code("18")
        assert ack_function == SystemFunction.ACK
        assert ack_function.value == "18"

        # Test NAK
        nak_function = SystemFunction.from_code("19")
        assert nak_function == SystemFunction.NAK
        assert nak_function.value == "19"

    def test_data_point_type_link_number(self):
        """Test LINK_NUMBER data point type."""
        link_number_type = DataPointType.from_code("04")
        assert link_number_type == DataPointType.LINK_NUMBER
        assert link_number_type.value == "04"

    def test_system_telegram_with_write_config_link_number(self):
        """Test SystemTelegram with write config for link number."""
        telegram = SystemTelegram(
            serial_number="0012345005",
            system_function=SystemFunction.WRITE_CONFIG,
            datapoint_type=DataPointType.LINK_NUMBER,
            checksum="FO",
            raw_telegram="<S0012345005F04D0425FO>",
        )

        assert telegram.serial_number == "0012345005"
        assert telegram.system_function == SystemFunction.WRITE_CONFIG
        assert telegram.datapoint_type == DataPointType.LINK_NUMBER
        assert telegram.checksum == "FO"
        assert telegram.raw_telegram == "<S0012345005F04D0425FO>"

    def test_system_telegram_with_read_config_link_number(self):
        """Test SystemTelegram with read config for link number."""
        telegram = SystemTelegram(
            serial_number="0012345005",
            system_function=SystemFunction.READ_CONFIG,
            datapoint_type=DataPointType.LINK_NUMBER,
            checksum="AB",
            raw_telegram="<S0012345005F03D04AB>",
        )

        assert telegram.system_function is not None
        assert telegram.datapoint_type is not None

        assert telegram.system_function.name == "READ_CONFIG"
        assert telegram.datapoint_type.name == "LINK_NUMBER"

    def test_function_descriptions(self):
        """Test human-readable function descriptions."""
        # Test existing functions
        write_config_telegram = SystemTelegram(
            serial_number="0012345005",
            system_function=SystemFunction.WRITE_CONFIG,
            datapoint_type=DataPointType.LINK_NUMBER,
            checksum="FO",
            raw_telegram="<S0012345005F04D0425FO>",
        )

        assert write_config_telegram.system_function is not None
        assert write_config_telegram.system_function.name == "WRITE_CONFIG"

        read_config_telegram = SystemTelegram(
            serial_number="0012345005",
            system_function=SystemFunction.READ_CONFIG,
            datapoint_type=DataPointType.LINK_NUMBER,
            checksum="AB",
            raw_telegram="<S0012345005F03D04AB>",
        )

        assert read_config_telegram.system_function is not None
        assert read_config_telegram.system_function.name == "READ_CONFIG"

        # Test new ACK/NAK functions
        ack_telegram = SystemTelegram(
            serial_number="0012345005",
            system_function=SystemFunction.ACK,
            datapoint_type=DataPointType.MODULE_TYPE,
            checksum="FB",
            raw_telegram="<R0012345005F18DFB>",
        )

        assert ack_telegram.system_function is not None
        assert ack_telegram.system_function.name == "ACK"

        nak_telegram = SystemTelegram(
            serial_number="0012345005",
            system_function=SystemFunction.NAK,
            datapoint_type=DataPointType.MODULE_TYPE,
            checksum="FA",
            raw_telegram="<R0012345005F19DFA>",
        )

        assert nak_telegram.system_function is not None
        assert nak_telegram.system_function.name == "NAK"

    def test_data_point_descriptions(self):
        """Test human-readable data point descriptions."""
        telegram = SystemTelegram(
            serial_number="0012345005",
            system_function=SystemFunction.WRITE_CONFIG,
            datapoint_type=DataPointType.LINK_NUMBER,
            checksum="FO",
            raw_telegram="<S0012345005F04D0425FO>",
        )

        assert telegram.datapoint_type is not None
        assert telegram.datapoint_type.name == "LINK_NUMBER"

        # Test that existing data points still work
        temp_telegram = SystemTelegram(
            serial_number="0012345005",
            system_function=SystemFunction.READ_CONFIG,
            datapoint_type=DataPointType.TEMPERATURE,
            checksum="AB",
            raw_telegram="<S0012345005F03D18AB>",
        )

        assert temp_telegram.datapoint_type is not None
        assert temp_telegram.datapoint_type.name == "TEMPERATURE"

    def test_to_dict_with_link_number(self):
        """Test dictionary conversion with link number data."""
        telegram = SystemTelegram(
            serial_number="0012345005",
            system_function=SystemFunction.WRITE_CONFIG,
            datapoint_type=DataPointType.LINK_NUMBER,
            checksum="FO",
            raw_telegram="<S0012345005F04D0425FO>",
        )
        telegram.checksum_validated = True

        result = telegram.to_dict()

        assert result["serial_number"] == "0012345005"
        assert result["system_function"]["code"] == "04"
        assert result["system_function"]["description"] == "WRITE_CONFIG"
        assert result["datapoint_type"]["code"] == "04"
        assert result["datapoint_type"]["description"] == "LINK_NUMBER"
        assert result["checksum"] == "FO"
        assert result["checksum_validated"] is True
        assert result["raw_telegram"] == "<S0012345005F04D0425FO>"
        assert result[("telegram_type")] == "S"

    def test_str_representation_with_link_number(self):
        """Test string representation with link number."""
        telegram = SystemTelegram(
            serial_number="0012345005",
            system_function=SystemFunction.WRITE_CONFIG,
            datapoint_type=DataPointType.LINK_NUMBER,
            checksum="FO",
            raw_telegram="<S0012345005F04D0425FO>",
        )

        str_repr = str(telegram)
        assert "WRITE_CONFIG" in str_repr
        assert "0012345005" in str_repr

    def test_all_system_functions_from_code(self):
        """Test that all system functions can be retrieved by code."""
        test_cases = [
            ("01", SystemFunction.DISCOVERY),
            ("02", SystemFunction.READ_DATAPOINT),
            ("03", SystemFunction.READ_CONFIG),
            ("04", SystemFunction.WRITE_CONFIG),
            ("05", SystemFunction.BLINK),
            ("06", SystemFunction.UNBLINK),
            ("18", SystemFunction.ACK),
            ("19", SystemFunction.NAK),
        ]

        for code, expected_function in test_cases:
            result = SystemFunction.from_code(code)
            assert result == expected_function

        # Test invalid code
        result = SystemFunction.from_code("99")
        assert result is None

    def test_all_data_point_types_from_code(self):
        """Test that all data point types can be retrieved by code."""
        test_cases = [
            ("00", DataPointType.MODULE_TYPE),
            ("04", DataPointType.LINK_NUMBER),
            ("18", DataPointType.TEMPERATURE),
            ("19", DataPointType.SW_TOP_VERSION),
            ("20", DataPointType.VOLTAGE),
            ("17", DataPointType.MODULE_ENERGY_LEVEL),
        ]

        for code, expected_type in test_cases:
            result = DataPointType.from_code(code)
            assert result == expected_type

        # Test invalid code
        result = DataPointType.from_code("99")
        assert result is None

    def test_timestamp_auto_generation(self):
        """Test that timestamp is automatically generated."""
        before_creation = datetime.now()

        telegram = SystemTelegram(
            serial_number="0012345005",
            system_function=SystemFunction.WRITE_CONFIG,
            datapoint_type=DataPointType.LINK_NUMBER,
            checksum="FO",
            raw_telegram="<S0012345005F04D0425FO>",
        )

        after_creation = datetime.now()

        assert telegram.timestamp is not None
        assert before_creation <= telegram.timestamp <= after_creation

        # Test with explicit timestamp
        explicit_time = datetime(2023, 1, 1, 12, 0, 0)
        telegram_with_time = SystemTelegram(
            serial_number="0012345005",
            system_function=SystemFunction.WRITE_CONFIG,
            datapoint_type=DataPointType.LINK_NUMBER,
            checksum="FO",
            raw_telegram="<S0012345005F04D0425FO>",
            timestamp=explicit_time,
        )

        assert telegram_with_time.timestamp == explicit_time

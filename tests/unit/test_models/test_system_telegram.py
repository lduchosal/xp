"""Unit tests for SystemTelegram model.

Tests the system telegram model functionality including parsing,
validation, and data structure integrity.
"""

import pytest
from datetime import datetime
from src.xp.models.system_telegram import (
    SystemTelegram, SystemFunction, DataPointType
)


class TestSystemFunction:
    """Test SystemFunction enum."""
    
    def test_from_code_valid(self):
        """Test from_code with valid codes."""
        assert SystemFunction.from_code("02") == SystemFunction.RETURN_DATA
        assert SystemFunction.from_code("01") == SystemFunction.UPDATE_FIRMWARE
        assert SystemFunction.from_code("03") == SystemFunction.READ_CONFIG
        assert SystemFunction.from_code("04") == SystemFunction.WRITE_CONFIG
        assert SystemFunction.from_code("05") == SystemFunction.SYSTEM_RESET
    
    def test_from_code_invalid(self):
        """Test from_code with invalid codes."""
        assert SystemFunction.from_code("99") is None
        assert SystemFunction.from_code("XX") is None
        assert SystemFunction.from_code("") is None
    
    def test_enum_values(self):
        """Test enum values are correct."""
        assert SystemFunction.RETURN_DATA.value == "02"
        assert SystemFunction.UPDATE_FIRMWARE.value == "01"
        assert SystemFunction.READ_CONFIG.value == "03"
        assert SystemFunction.WRITE_CONFIG.value == "04"
        assert SystemFunction.SYSTEM_RESET.value == "05"


class TestDataPointType:
    """Test DataPointType enum."""
    
    def test_from_code_valid(self):
        """Test from_code with valid codes."""
        assert DataPointType.from_code("18") == DataPointType.TEMPERATURE
        assert DataPointType.from_code("19") == DataPointType.HUMIDITY
        assert DataPointType.from_code("20") == DataPointType.VOLTAGE
        assert DataPointType.from_code("21") == DataPointType.CURRENT
        assert DataPointType.from_code("00") == DataPointType.STATUS
    
    def test_from_code_invalid(self):
        """Test from_code with invalid codes."""
        assert DataPointType.from_code("99") is None
        assert DataPointType.from_code("XX") is None
        assert DataPointType.from_code("") is None
    
    def test_enum_values(self):
        """Test enum values are correct."""
        assert DataPointType.TEMPERATURE.value == "18"
        assert DataPointType.HUMIDITY.value == "19"
        assert DataPointType.VOLTAGE.value == "20"
        assert DataPointType.CURRENT.value == "21"
        assert DataPointType.STATUS.value == "00"


class TestSystemTelegram:
    """Test SystemTelegram model."""
    
    def test_system_telegram_creation(self):
        """Test basic system telegram creation."""
        telegram = SystemTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.RETURN_DATA,
            data_point_id=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>"
        )
        
        assert telegram.serial_number == "0020012521"
        assert telegram.system_function == SystemFunction.RETURN_DATA
        assert telegram.data_point_id == DataPointType.TEMPERATURE
        assert telegram.checksum == "FN"
        assert telegram.raw_telegram == "<S0020012521F02D18FN>"
        assert telegram.timestamp is not None
        assert isinstance(telegram.timestamp, datetime)
    
    def test_system_telegram_with_timestamp(self):
        """Test system telegram creation with explicit timestamp."""
        test_time = datetime(2023, 1, 1, 12, 0, 0)
        telegram = SystemTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.RETURN_DATA,
            data_point_id=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>",
            timestamp=test_time
        )
        
        assert telegram.timestamp == test_time
    
    def test_function_description(self):
        """Test function description property."""
        telegram = SystemTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.RETURN_DATA,
            data_point_id=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>"
        )
        
        assert telegram.function_description == "Return Data"
        
        # Test other functions
        telegram.system_function = SystemFunction.UPDATE_FIRMWARE
        assert telegram.function_description == "Update Firmware"
        
        telegram.system_function = SystemFunction.READ_CONFIG
        assert telegram.function_description == "Read Configuration"
    
    def test_data_point_description(self):
        """Test data point description property."""
        telegram = SystemTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.RETURN_DATA,
            data_point_id=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>"
        )
        
        assert telegram.data_point_description == "Temperature"
        
        # Test other data points
        telegram.data_point_id = DataPointType.HUMIDITY
        assert telegram.data_point_description == "Humidity"
        
        telegram.data_point_id = DataPointType.VOLTAGE
        assert telegram.data_point_description == "Voltage"
        
        telegram.data_point_id = DataPointType.CURRENT
        assert telegram.data_point_description == "Current"
        
        telegram.data_point_id = DataPointType.STATUS
        assert telegram.data_point_description == "Status"
    
    def test_to_dict(self):
        """Test to_dict method."""
        telegram = SystemTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.RETURN_DATA,
            data_point_id=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>"
        )
        
        result = telegram.to_dict()
        
        assert isinstance(result, dict)
        assert result["serial_number"] == "0020012521"
        assert result["system_function"]["code"] == "02"
        assert result["system_function"]["description"] == "Return Data"
        assert result["data_point_id"]["code"] == "18"
        assert result["data_point_id"]["description"] == "Temperature"
        assert result["checksum"] == "FN"
        assert result["raw_telegram"] == "<S0020012521F02D18FN>"
        assert result["telegram_type"] == "system"
        assert "timestamp" in result
        assert result["timestamp"] is not None
    
    def test_str_representation(self):
        """Test string representation."""
        telegram = SystemTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.RETURN_DATA,
            data_point_id=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>"
        )
        
        str_repr = str(telegram)
        
        assert "System Telegram" in str_repr
        assert "Return Data" in str_repr
        assert "Temperature" in str_repr
        assert "0020012521" in str_repr
    
    @pytest.mark.parametrize("function,description", [
        (SystemFunction.RETURN_DATA, "Return Data"),
        (SystemFunction.UPDATE_FIRMWARE, "Update Firmware"),
        (SystemFunction.READ_CONFIG, "Read Configuration"),
        (SystemFunction.WRITE_CONFIG, "Write Configuration"),
        (SystemFunction.SYSTEM_RESET, "System Reset")
    ])
    def test_function_descriptions(self, function, description):
        """Test all function descriptions."""
        telegram = SystemTelegram(
            serial_number="0020012521",
            system_function=function,
            data_point_id=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>"
        )
        
        assert telegram.function_description == description
    
    @pytest.mark.parametrize("data_point,description", [
        (DataPointType.TEMPERATURE, "Temperature"),
        (DataPointType.HUMIDITY, "Humidity"),
        (DataPointType.VOLTAGE, "Voltage"),
        (DataPointType.CURRENT, "Current"),
        (DataPointType.STATUS, "Status")
    ])
    def test_data_point_descriptions(self, data_point, description):
        """Test all data point descriptions."""
        telegram = SystemTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.RETURN_DATA,
            data_point_id=data_point,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>"
        )
        
        assert telegram.data_point_description == description
    
    def test_telegram_equality(self):
        """Test telegram object equality."""
        timestamp = datetime.now()
        
        telegram1 = SystemTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.RETURN_DATA,
            data_point_id=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>",
            timestamp=timestamp
        )
        
        telegram2 = SystemTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.RETURN_DATA,
            data_point_id=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>",
            timestamp=timestamp
        )
        
        # Dataclass should provide equality
        assert telegram1 == telegram2
    
    def test_telegram_with_different_serial_numbers(self):
        """Test telegrams with different serial numbers."""
        telegram1 = SystemTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.RETURN_DATA,
            data_point_id=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>"
        )
        
        telegram2 = SystemTelegram(
            serial_number="1234567890",
            system_function=SystemFunction.RETURN_DATA,
            data_point_id=DataPointType.TEMPERATURE,
            checksum="AB",
            raw_telegram="<S1234567890F02D18AB>"
        )
        
        assert telegram1.serial_number != telegram2.serial_number
        assert telegram1.checksum != telegram2.checksum
        assert telegram1.raw_telegram != telegram2.raw_telegram
    
    def test_post_init_timestamp_generation(self):
        """Test that __post_init__ sets timestamp if not provided."""
        before = datetime.now()
        
        telegram = SystemTelegram(
            serial_number="0020012521",
            system_function=SystemFunction.RETURN_DATA,
            data_point_id=DataPointType.TEMPERATURE,
            checksum="FN",
            raw_telegram="<S0020012521F02D18FN>"
        )
        
        after = datetime.now()
        
        assert before <= telegram.timestamp <= after
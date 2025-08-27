import pytest
import click
from src.xp.cli.validators import (
    validate_telegram_format,
    validate_telegram_string,
    validate_input_range,
    validate_data_stream,
    TelegramValidator
)


class TestValidators:
    """Test cases for CLI validators"""
    
    def test_validate_telegram_string_valid_formats(self):
        """Test validation of valid telegram strings"""
        valid_telegrams = [
            "<E14L00I02MAK>",
            "<E1L00I02MAK>",
            "<E99L99I90B99>",
            "<E5L15I25M00>",
        ]
        
        for telegram in valid_telegrams:
            assert validate_telegram_string(telegram) is True
    
    def test_validate_telegram_string_invalid_formats(self):
        """Test validation of invalid telegram strings"""
        invalid_telegrams = [
            "",
            "E14L00I02MAK>",
            "<E14L00I02MAK",
            "<X14L00I02MAK>",
            "<E14X00I02MAK>",
            "<E14L00X02MAK>",
            "<E14L00I02XAK>",
            "<E14L00I02MA>",
            "<E14L00I02MAKX>",
            "<E100L00I02MAK>",  # Module type too long
        ]
        
        for telegram in invalid_telegrams:
            assert validate_telegram_string(telegram) is False
    
    def test_validate_telegram_string_with_whitespace(self):
        """Test validation handles whitespace correctly"""
        assert validate_telegram_string("  <E14L00I02MAK>  ") is True
        assert validate_telegram_string("  <E14L00I02MAK") is False
    
    def test_validate_input_range_valid(self):
        """Test input range validation with valid values"""
        # Should not raise exception
        validate_input_range(5, 1, 10, "test_field")
        validate_input_range(1, 1, 10, "test_field")
        validate_input_range(10, 1, 10, "test_field")
    
    def test_validate_input_range_invalid(self):
        """Test input range validation with invalid values"""
        with pytest.raises(click.BadParameter, match="test_field must be between 1 and 10, got 0"):
            validate_input_range(0, 1, 10, "test_field")
        
        with pytest.raises(click.BadParameter, match="test_field must be between 1 and 10, got 11"):
            validate_input_range(11, 1, 10, "test_field")
    
    def test_validate_data_stream_valid(self):
        """Test data stream validation with valid streams"""
        valid_streams = [
            "<E14L00I02MAK>",
            "Some data <E14L00I02MAK> more data",
            "Multiple <E14L00I02MAK> telegrams <E14L01I03BB1>",
        ]
        
        for stream in valid_streams:
            assert validate_data_stream(stream) is True
    
    def test_validate_data_stream_invalid(self):
        """Test data stream validation with invalid streams"""
        invalid_streams = [
            "",
            "No telegrams here",
            "<INVALID_FORMAT>",
            "Almost <E14L00I02MA> but not quite",
        ]
        
        for stream in invalid_streams:
            assert validate_data_stream(stream) is False
    
    def test_validate_telegram_format_decorator_valid(self):
        """Test telegram format decorator with valid input"""
        @validate_telegram_format
        def dummy_function(telegram_string):
            return f"Processed: {telegram_string}"
        
        result = dummy_function("<E14L00I02MAK>")
        assert result == "Processed: <E14L00I02MAK>"
    
    def test_validate_telegram_format_decorator_invalid(self):
        """Test telegram format decorator with invalid input"""
        @validate_telegram_format
        def dummy_function(telegram_string):
            return f"Processed: {telegram_string}"
        
        with pytest.raises(click.BadParameter, match="Invalid telegram format"):
            dummy_function("INVALID")
    
    def test_validate_telegram_format_decorator_kwargs(self):
        """Test telegram format decorator with kwargs"""
        @validate_telegram_format
        def dummy_function(telegram_string=None):
            return f"Processed: {telegram_string}"
        
        result = dummy_function(telegram_string="<E14L00I02MAK>")
        assert result == "Processed: <E14L00I02MAK>"


class TestTelegramValidator:
    """Test cases for TelegramValidator class"""
    
    def test_validate_module_type_valid(self):
        """Test module type validation with valid values"""
        # Should not raise exception
        TelegramValidator.validate_module_type(1)
        TelegramValidator.validate_module_type(14)
        TelegramValidator.validate_module_type(99)
    
    def test_validate_module_type_invalid(self):
        """Test module type validation with invalid values"""
        with pytest.raises(click.BadParameter, match="Module type must be between 1 and 99"):
            TelegramValidator.validate_module_type(0)
        
        with pytest.raises(click.BadParameter, match="Module type must be between 1 and 99"):
            TelegramValidator.validate_module_type(100)
    
    def test_validate_link_number_valid(self):
        """Test link number validation with valid values"""
        # Should not raise exception
        TelegramValidator.validate_link_number(0)
        TelegramValidator.validate_link_number(50)
        TelegramValidator.validate_link_number(99)
    
    def test_validate_link_number_invalid(self):
        """Test link number validation with invalid values"""
        with pytest.raises(click.BadParameter, match="Link number must be between 0 and 99"):
            TelegramValidator.validate_link_number(-1)
        
        with pytest.raises(click.BadParameter, match="Link number must be between 0 and 99"):
            TelegramValidator.validate_link_number(100)
    
    def test_validate_input_number_valid(self):
        """Test input number validation with valid values"""
        # Should not raise exception
        TelegramValidator.validate_input_number(0)
        TelegramValidator.validate_input_number(45)
        TelegramValidator.validate_input_number(90)
    
    def test_validate_input_number_invalid(self):
        """Test input number validation with invalid values"""
        with pytest.raises(click.BadParameter, match="Input number must be between 0 and 90"):
            TelegramValidator.validate_input_number(-1)
        
        with pytest.raises(click.BadParameter, match="Input number must be between 0 and 90"):
            TelegramValidator.validate_input_number(91)
    
    def test_validate_event_type_valid(self):
        """Test event type validation with valid values"""
        # Should not raise exception
        TelegramValidator.validate_event_type("M")
        TelegramValidator.validate_event_type("B")
    
    def test_validate_event_type_invalid(self):
        """Test event type validation with invalid values"""
        with pytest.raises(click.BadParameter, match="Event type must be 'M' or 'B'"):
            TelegramValidator.validate_event_type("X")
        
        with pytest.raises(click.BadParameter, match="Event type must be 'M' or 'B'"):
            TelegramValidator.validate_event_type("m")
    
    def test_validate_checksum_valid(self):
        """Test checksum validation with valid values"""
        # Should not raise exception
        TelegramValidator.validate_checksum("AK")
        TelegramValidator.validate_checksum("B1")
        TelegramValidator.validate_checksum("00")
        TelegramValidator.validate_checksum("ZZ")
    
    def test_validate_checksum_invalid_length(self):
        """Test checksum validation with invalid lengths"""
        with pytest.raises(click.BadParameter, match="Checksum must be exactly 2 characters"):
            TelegramValidator.validate_checksum("A")
        
        with pytest.raises(click.BadParameter, match="Checksum must be exactly 2 characters"):
            TelegramValidator.validate_checksum("AKX")
        
        with pytest.raises(click.BadParameter, match="Checksum must be exactly 2 characters"):
            TelegramValidator.validate_checksum("")
    
    def test_validate_checksum_invalid_characters(self):
        """Test checksum validation with invalid characters"""
        with pytest.raises(click.BadParameter, match="Checksum must contain only alphanumeric characters"):
            TelegramValidator.validate_checksum("A!")
        
        with pytest.raises(click.BadParameter, match="Checksum must contain only alphanumeric characters"):
            TelegramValidator.validate_checksum("@#")
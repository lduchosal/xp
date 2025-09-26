"""Tests for LinkNumberService"""

import pytest
from xp.services.telegram_link_number_service import LinkNumberService, LinkNumberError
from xp.models.system_telegram import SystemTelegram
from xp.models.datapoint_type import DataPointType
from xp.models.system_function import SystemFunction
from xp.models.reply_telegram import ReplyTelegram
from unittest.mock import Mock


class TestLinkNumberService:
    """Test cases for LinkNumberService"""

    def test_init(self):
        """Test initialization"""
        service = LinkNumberService()
        assert isinstance(service, LinkNumberService)

    def test_generate_set_link_number_telegram_valid(self):
        """Test generating valid set link number telegram"""
        service = LinkNumberService()

        # Test case from specification
        result = service.generate_set_link_number_telegram("0012345005", 25)
        assert result == "<S0012345005F04D0425FC>"

        # Test another case
        result = service.generate_set_link_number_telegram("0012345005", 9)
        assert result == "<S0012345005F04D0409FM>"

        # Test with leading zero
        result = service.generate_set_link_number_telegram("0012345005", 5)
        assert result == "<S0012345005F04D0405FA>"

        # Test boundary values
        result = service.generate_set_link_number_telegram("1234567890", 0)
        assert result == "<S1234567890F04D0400FA>"

        result = service.generate_set_link_number_telegram("1234567890", 99)
        assert result == "<S1234567890F04D0499FA>"

    def test_generate_set_link_number_telegram_invalid_serial(self):
        """Test generating telegram with invalid serial number"""
        service = LinkNumberService()

        # Test empty serial
        with pytest.raises(LinkNumberError, match="Serial number must be 10 digits"):
            service.generate_set_link_number_telegram("", 25)

        # Test short serial
        with pytest.raises(LinkNumberError, match="Serial number must be 10 digits"):
            service.generate_set_link_number_telegram("123456789", 25)

        # Test long serial
        with pytest.raises(LinkNumberError, match="Serial number must be 10 digits"):
            service.generate_set_link_number_telegram("12345678901", 25)

        # Test non-numeric serial
        with pytest.raises(
            LinkNumberError, match="Serial number must contain only digits"
        ):
            service.generate_set_link_number_telegram("123456789A", 25)

    def test_generate_set_link_number_telegram_invalid_link_number(self):
        """Test generating telegram with invalid link number"""
        service = LinkNumberService()

        # Test negative link number
        with pytest.raises(LinkNumberError, match="Link number must be between 0-99"):
            service.generate_set_link_number_telegram("0012345005", -1)

        # Test link number too high
        with pytest.raises(LinkNumberError, match="Link number must be between 0-99"):
            service.generate_set_link_number_telegram("0012345005", 100)

    def test_generate_read_link_number_telegram_valid(self):
        """Test generating valid read link number telegram"""
        result = LinkNumberService().generate_read_link_number_telegram("0012345005")
        assert result.startswith("<S0012345005F03D04")
        assert result.endswith(">")
        assert len(result) == 21  # <S{10}F03D04{2}> = 21 chars

    def test_generate_read_link_number_telegram_invalid_serial(self):
        """Test generating read telegram with invalid serial number"""
        service = LinkNumberService()

        # Test invalid serials (same validation as set)
        with pytest.raises(LinkNumberError, match="Serial number must be 10 digits"):
            service.generate_read_link_number_telegram("123")

        with pytest.raises(
            LinkNumberError, match="Serial number must contain only digits"
        ):
            service.generate_read_link_number_telegram("123456789A")

    def test_create_set_link_number_telegram_object(self):
        """Test creating SystemTelegram object for set operation"""
        telegram = LinkNumberService().create_set_link_number_telegram_object(
            "0012345005", 25
        )

        assert isinstance(telegram, SystemTelegram)
        assert telegram.serial_number == "0012345005"
        assert telegram.system_function == SystemFunction.WRITE_CONFIG
        assert telegram.datapoint_type == DataPointType.LINK_NUMBER
        assert telegram.raw_telegram == "<S0012345005F04D0425FC>"
        assert telegram.checksum == "FC"

    def test_create_read_link_number_telegram_object(self):
        """Test creating SystemTelegram object for read operation"""
        telegram = LinkNumberService().create_read_link_number_telegram_object(
            "0012345005"
        )

        assert isinstance(telegram, SystemTelegram)
        assert telegram.serial_number == "0012345005"
        assert telegram.system_function == SystemFunction.READ_CONFIG
        assert telegram.datapoint_type == DataPointType.LINK_NUMBER
        assert telegram.raw_telegram.startswith("<S0012345005F03D04")
        assert len(telegram.checksum) == 2

    def test_parse_link_number_from_reply_valid(self):
        """Test parsing link number from valid reply telegram"""
        service = LinkNumberService()

        # Create a mock reply telegram with link number data
        reply_telegram = Mock(spec=ReplyTelegram)
        reply_telegram.datapoint_type = DataPointType.LINK_NUMBER
        reply_telegram.data_value = "25"

        result = service.parse_link_number_from_reply(reply_telegram)
        assert result == 25

        # Test with zero
        reply_telegram.data_value = "0"
        result = service.parse_link_number_from_reply(reply_telegram)
        assert result == 0

        # Test with max value
        reply_telegram.data_value = "99"
        result = service.parse_link_number_from_reply(reply_telegram)
        assert result == 99

    def test_parse_link_number_from_reply_invalid(self):
        """Test parsing link number from invalid reply telegram"""
        service = LinkNumberService()

        # Wrong data point type
        reply_telegram = Mock(spec=ReplyTelegram)
        reply_telegram.datapoint_type = DataPointType.TEMPERATURE
        reply_telegram.data_value = "25"

        result = service.parse_link_number_from_reply(reply_telegram)
        assert result is None

        # No data value
        reply_telegram.datapoint_type = DataPointType.LINK_NUMBER
        reply_telegram.data_value = None

        result = service.parse_link_number_from_reply(reply_telegram)
        assert result is None

        # Non-numeric data value
        reply_telegram.data_value = "ABC"

        result = service.parse_link_number_from_reply(reply_telegram)
        assert result is None

        # Out of range value
        reply_telegram.data_value = "150"

        result = service.parse_link_number_from_reply(reply_telegram)
        assert result is None

        # Negative value
        reply_telegram.data_value = "-1"

        result = service.parse_link_number_from_reply(reply_telegram)
        assert result is None

    def test_is_ack_response(self):
        """Test identifying ACK responses"""
        service = LinkNumberService()

        # Create mock ACK response
        ack_reply = Mock(spec=ReplyTelegram)
        ack_reply.system_function = SystemFunction.ACK

        assert service.is_ack_response(ack_reply) is True

        # Create mock non-ACK response
        nak_reply = Mock(spec=ReplyTelegram)
        nak_reply.system_function = SystemFunction.NAK

        assert service.is_ack_response(nak_reply) is False

        # Create mock other response
        other_reply = Mock(spec=ReplyTelegram)
        other_reply.system_function = SystemFunction.READ_DATAPOINT

        assert service.is_ack_response(other_reply) is False

    def test_is_nak_response(self):
        """Test identifying NAK responses"""
        service = LinkNumberService()

        # Create mock NAK response
        nak_reply = Mock(spec=ReplyTelegram)
        nak_reply.system_function = SystemFunction.NAK

        assert service.is_nak_response(nak_reply) is True

        # Create mock non-NAK response
        ack_reply = Mock(spec=ReplyTelegram)
        ack_reply.system_function = SystemFunction.ACK

        assert service.is_nak_response(ack_reply) is False

        # Create mock other response
        other_reply = Mock(spec=ReplyTelegram)
        other_reply.system_function = SystemFunction.READ_DATAPOINT

        assert service.is_nak_response(other_reply) is False

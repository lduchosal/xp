"""Tests for BlinkService."""

from unittest.mock import Mock

import pytest

from xp.models.telegram.reply_telegram import ReplyTelegram
from xp.models.telegram.system_function import SystemFunction
from xp.models.telegram.system_telegram import SystemTelegram
from xp.services.telegram.telegram_blink_service import BlinkError, TelegramBlinkService


class TestBlinkService:
    """Test cases for BlinkService."""

    def test_init(self):
        """Test initialization."""
        service = TelegramBlinkService()
        assert isinstance(service, TelegramBlinkService)

    def test_generate_blink_telegram_valid(self):
        """Test generating valid blink telegram."""
        service = TelegramBlinkService()

        # Test case from specification: <S0012345008F05D00FN>
        result = service.generate_blink_telegram("0012345008", "on")
        assert result == "<S0012345008F05D00FN>"

        # Test another case
        result = service.generate_blink_telegram("0012345011", "on")
        assert result == "<S0012345011F05D00FF>"

        # Test different serial numbers
        result = service.generate_blink_telegram("1234567890", "on")
        assert result.startswith("<S1234567890F05D00")
        assert result.endswith(">")
        assert len(result) == 21  # <S{10}F05D00{2}> = 21 chars

    def test_generate_blink_telegram_invalid_serial(self):
        """Test generating blink telegram with invalid serial number."""
        service = TelegramBlinkService()

        # Test empty serial
        with pytest.raises(BlinkError, match="Serial number must be 10 digits"):
            service.generate_blink_telegram("", "on")

        # Test short serial
        with pytest.raises(BlinkError, match="Serial number must be 10 digits"):
            service.generate_blink_telegram("123456789", "on")

        # Test long serial
        with pytest.raises(BlinkError, match="Serial number must be 10 digits"):
            service.generate_blink_telegram("12345678901", "on")

        # Test non-numeric serial
        with pytest.raises(BlinkError, match="Serial number must contain only digits"):
            service.generate_blink_telegram("123456789A", "on")

    def test_generate_unblink_telegram_valid(self):
        """Test generating valid unblink telegram."""
        service = TelegramBlinkService()

        # Test case from specification: <S0012345011F06D00FK>
        result = service.generate_blink_telegram("0012345011", "off")
        assert result == "<S0012345011F06D00FG>"

        # Test another case
        result = service.generate_blink_telegram("0012345008", "off")
        assert result == "<S0012345008F06D00FO>"

        # Test different serial numbers
        result = service.generate_blink_telegram("1234567890", "off")
        assert result.startswith("<S1234567890F06D00")
        assert result.endswith(">")
        assert len(result) == 21  # <S{10}F06D00{2}> = 21 chars

    def test_generate_unblink_telegram_invalid_serial(self):
        """Test generating unblink telegram with invalid serial number."""
        service = TelegramBlinkService()

        # Test empty serial
        with pytest.raises(BlinkError, match="Serial number must be 10 digits"):
            service.generate_blink_telegram("", "off")

        # Test short serial
        with pytest.raises(BlinkError, match="Serial number must be 10 digits"):
            service.generate_blink_telegram("123456789", "off")

        # Test long serial
        with pytest.raises(BlinkError, match="Serial number must be 10 digits"):
            service.generate_blink_telegram("12345678901", "off")

        # Test non-numeric serial
        with pytest.raises(BlinkError, match="Serial number must contain only digits"):
            service.generate_blink_telegram("123456789A", "off")

    def test_create_blink_telegram_object(self):
        """Test creating SystemTelegram object for blink operation."""
        telegram = TelegramBlinkService().create_blink_telegram_object("0012345008")

        assert isinstance(telegram, SystemTelegram)
        assert telegram.serial_number == "0012345008"
        assert telegram.system_function == SystemFunction.BLINK
        assert telegram.datapoint_type is None
        assert telegram.raw_telegram == "<S0012345008F05D00FN>"
        assert telegram.checksum == "FN"

    def test_create_unblink_telegram_object(self):
        """Test creating SystemTelegram object for unblink operation."""
        telegram = TelegramBlinkService().create_unblink_telegram_object("0012345011")

        assert isinstance(telegram, SystemTelegram)
        assert telegram.serial_number == "0012345011"
        assert telegram.system_function == SystemFunction.UNBLINK
        assert telegram.datapoint_type is None
        assert telegram.raw_telegram == "<S0012345011F06D00FG>"
        assert telegram.checksum == "FG"

    def test_is_ack_response(self):
        """Test identifying ACK responses."""
        service = TelegramBlinkService()

        # Create mock ACK response (F18D from spec)
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
        """Test identifying NAK responses."""
        service = TelegramBlinkService()

        # Create mock NAK response (F19D from spec)
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

    def test_blink_unblink_telegram_format(self):
        """Test that generated telegrams follow correct format."""
        service = TelegramBlinkService()

        # Test blink telegram structure
        blink_telegram = service.generate_blink_telegram("0012345008", "on")
        assert blink_telegram.startswith("<S")
        assert "F05D00" in blink_telegram
        assert blink_telegram.endswith(">")

        # Test unblink telegram structure
        unblink_telegram = service.generate_blink_telegram("0012345011", "off")
        assert unblink_telegram.startswith("<S")
        assert "F06D00" in unblink_telegram
        assert unblink_telegram.endswith(">")

    def test_different_serial_numbers(self):
        """Test blink/unblink with various serial numbers."""
        service = TelegramBlinkService()

        test_serials = [
            "0000000000",
            "0012345008",
            "0012345011",
            "1234567890",
            "9999999999",
        ]

        for serial in test_serials:
            blink_telegram = service.generate_blink_telegram(serial, "on")
            unblink_telegram = service.generate_blink_telegram(serial, "off")

            assert f"S{serial}" in blink_telegram
            assert f"S{serial}" in unblink_telegram
            assert "F05D00" in blink_telegram
            assert "F06D00" in unblink_telegram

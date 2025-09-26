import pytest

from xp.services.conbus_service import ConbusService


class TestConbusServiceTelegramParsing:
    """Test cases for ConbusService telegram parsing functionality"""

    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        return ConbusService()

    def test_parse_telegrams_empty_data(self, service):
        """Test parsing empty data"""
        result = service._parse_telegrams("")
        assert result == []

    def test_parse_telegrams_single_telegram(self, service):
        """Test parsing single complete telegram"""
        raw_data = "<S0020012521F02D18FN>"
        result = service._parse_telegrams(raw_data)
        assert result == ["<S0020012521F02D18FN>"]

    def test_parse_telegrams_multiple_telegrams(self, service):
        """Test parsing multiple complete telegrams"""
        raw_data = "<S0020012521F02D18FN><R0020012521F02D18+26,0§CIL>"
        result = service._parse_telegrams(raw_data)
        assert result == ["<S0020012521F02D18FN>", "<R0020012521F02D18+26,0§CIL>"]

    def test_parse_telegrams_with_whitespace(self, service):
        """Test parsing telegrams with surrounding whitespace"""
        raw_data = "  <S0020012521F02D18FN>  \n  <R0020012521F02D18+26,0§CIL>  "
        result = service._parse_telegrams(raw_data)
        assert result == ["<S0020012521F02D18FN>", "<R0020012521F02D18+26,0§CIL>"]

    def test_parse_telegrams_incomplete_telegram(self, service):
        """Test parsing incomplete telegram (missing closing >)"""
        raw_data = "<S0020012521F02D18FN"
        result = service._parse_telegrams(raw_data)
        assert result == []

    def test_parse_telegrams_malformed_start(self, service):
        """Test parsing telegram with malformed start (missing opening <)"""
        raw_data = "S0020012521F02D18FN>"
        result = service._parse_telegrams(raw_data)
        assert result == []

    def test_parse_telegrams_mixed_complete_incomplete(self, service):
        """Test parsing mix of complete and incomplete telegrams"""
        raw_data = "<S0020012521F02D18FN><R0020012521F02D18+26,0§CIL><INCOMPLETE"
        result = service._parse_telegrams(raw_data)
        assert result == ["<S0020012521F02D18FN>", "<R0020012521F02D18+26,0§CIL>"]

    def test_parse_telegrams_with_text_between(self, service):
        """Test parsing telegrams with text between them"""
        raw_data = "<TELEGRAM1>some text here<TELEGRAM2>more text<TELEGRAM3>"
        result = service._parse_telegrams(raw_data)
        assert result == ["<TELEGRAM1>", "<TELEGRAM2>", "<TELEGRAM3>"]

    def test_parse_telegrams_split_scenario(self, service):
        """Test the main use case: telegrams split across TCP packets"""
        # Simulating what would happen if TCP packets arrive split
        packet1 = "<S0020012"
        packet2 = "521F02D18FN><R002001252"
        packet3 = "1F02D18+26,0§CIL>"

        # Accumulated data as it would be received
        accumulated_data = packet1 + packet2 + packet3
        result = service._parse_telegrams(accumulated_data)

        assert result == ["<S0020012521F02D18FN>", "<R0020012521F02D18+26,0§CIL>"]

    def test_parse_telegrams_nested_brackets(self, service):
        """Test parsing telegrams that might contain < or > characters inside"""
        raw_data = "<DATA<>INSIDE><ANOTHER>DATA>"
        result = service._parse_telegrams(raw_data)
        # Should parse based on outermost brackets
        assert result == ["<DATA<>", "<ANOTHER>"]

    def test_parse_telegrams_empty_telegram(self, service):
        """Test parsing empty telegram"""
        raw_data = "<><VALID_TELEGRAM>"
        result = service._parse_telegrams(raw_data)
        # Empty telegrams are still valid telegrams with content "<>"
        assert result == ["<>", "<VALID_TELEGRAM>"]

    def test_parse_telegrams_only_whitespace_telegram(self, service):
        """Test parsing telegram with only whitespace"""
        raw_data = "<   ><VALID_TELEGRAM>"
        result = service._parse_telegrams(raw_data)
        # Whitespace telegrams are preserved as valid content
        assert result == ["<   >", "<VALID_TELEGRAM>"]

    def test_parse_telegrams_real_world_example(self, service):
        """Test with real telegram examples from the codebase"""
        raw_data = "<E14L00I02MAK><S0020012521F02D18FN><R0020012521F02D18+26,0§CIL>"
        result = service._parse_telegrams(raw_data)
        assert result == [
            "<E14L00I02MAK>",
            "<S0020012521F02D18FN>",
            "<R0020012521F02D18+26,0§CIL>",
        ]

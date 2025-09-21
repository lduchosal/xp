from xp.services.xp33_server_service import XP33ServerService
from xp.models.system_telegram import SystemTelegram
from xp.models.datapoint_type import DataPointType
from xp.models.system_function import SystemFunction
from xp.services.telegram_service import TelegramService


class TestXP33ServerService:
    """Test cases for XP33ServerService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.xp33lr_service = XP33ServerService("0012345003", "XP33LR")
        self.xp33led_service = XP33ServerService("0020042797", "XP33LED")
        self.telegram_service = TelegramService()

    def test_init_xp33lr_variant(self):
        """Test XP33ServerService initialization for XP33LR variant"""
        service = XP33ServerService("0012345003", "XP33LR")

        assert service.serial_number == "0012345003"
        assert service.variant == "XP33LR"
        assert service.device_type == "XP33"
        assert service.firmware_version == "XP33LR_V0.00.00"
        assert service.ean_code == "1234567890124"
        assert service.max_power == 640
        assert service.device_status == "00"
        assert service.link_number == 4
        assert service.module_type_code == 30
        assert service.channel_states == [0, 0, 0]
        assert len(service.scenes) == 4

    def test_init_xp33led_variant(self):
        """Test XP33ServerService initialization for XP33LED variant"""
        service = XP33ServerService("0020042797", "XP33LED")

        assert service.serial_number == "0020042797"
        assert service.variant == "XP33LED"
        assert service.device_type == "XP33"
        assert service.firmware_version == "XP33LED_V0.00.00"
        assert service.ean_code == "1234567890123"
        assert service.max_power == 300
        assert service.device_status == "00"
        assert service.link_number == 4
        assert service.module_type_code == 31

    def test_generate_discover_response(self):
        """Test discover response generation"""
        response = self.xp33lr_service.generate_discover_response()

        assert response == "<R0012345003F01DFD>"
        assert response.startswith("<R")
        assert response.endswith(">")
        assert "0012345003" in response
        assert "F01D" in response

    def test_generate_version_response(self):
        """Test version response generation"""
        # Create system telegram for version request
        request = SystemTelegram(
            checksum="FN",
            raw_telegram="<S0012345003F02D02FN>",
            serial_number="0012345003",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.SW_VERSION,
        )

        response = self.xp33lr_service.generate_version_response(request)

        assert response == "<R0012345003F02D02XP33LR_V0.00.00HN>"
        assert "XP33LR_V0.00.00" in response

    def test_generate_version_response_led_variant(self):
        """Test version response for XP33LED variant"""
        request = SystemTelegram(
            checksum="FN",
            raw_telegram="<S0020042797F02D02FN>",
            serial_number="0020042797",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.SW_VERSION,
        )

        response = self.xp33led_service.generate_version_response(request)

        assert response is not None
        assert "XP33LED_V0.00.00" in response

    def test_generate_module_type_response(self):
        """Test module type response generation"""
        request = SystemTelegram(
            checksum="FI",
            raw_telegram="<S0012345003F02D07FI>",
            serial_number="0012345003",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_TYPE_CODE,
        )

        response = self.xp33lr_service.generate_module_type_response(request)

        assert response == "<R0012345003F02D0730FE>"
        assert "F02D07" in response
        assert "30" in response  # 30 decimal = 0x1E

    def test_generate_status_response(self):
        """Test status response generation"""
        request = SystemTelegram(
            checksum="FO",
            raw_telegram="<S0012345003F02D10FO>",
            serial_number="0012345003",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_ERROR_CODE,
        )

        response = self.xp33lr_service.generate_status_response(request)

        assert response == "<R0012345003F02D1000FB>"
        assert "F02D10" in response
        assert "00" in response  # Normal status

    def test_generate_channel_states_response(self):
        """Test channel states response generation"""
        request = SystemTelegram(
            checksum="FM",
            raw_telegram="<S0012345003F02D12FM>",
            serial_number="0012345003",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )

        response = self.xp33lr_service.generate_channel_states_response(request)

        assert response == "<R0012345003F02D12000000000GD>"
        assert "F02D12" in response
        assert "00000000" in response  # All channels at 0%

    def test_generate_link_number_response(self):
        """Test link number response generation"""
        request = SystemTelegram(
            checksum="FL",
            raw_telegram="<S0012345003F02D04FL>",
            serial_number="0012345003",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.LINK_NUMBER,
        )

        response = self.xp33lr_service.generate_link_number_response(request)

        assert response == "<R0012345003F02D0404FA>"
        assert "F02D04" in response
        assert "04" in response  # 4 links configured

    def test_generate_link_number_response_legacy_alias(self):
        """Test link number response with legacy LINK_NUMBER alias"""
        request = SystemTelegram(
            checksum="FL",
            raw_telegram="<S0012345003F02D04FL>",
            serial_number="0012345003",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.LINK_NUMBER,
        )

        response = self.xp33lr_service.generate_link_number_response(request)

        assert response == "<R0012345003F02D0404FA>"

    def test_set_channel_dimming_valid(self):
        """Test setting channel dimming levels within valid range"""
        assert self.xp33lr_service.set_channel_dimming(1, 50) is True
        assert self.xp33lr_service.set_channel_dimming(2, 75) is True
        assert self.xp33lr_service.set_channel_dimming(3, 25) is True

        assert self.xp33lr_service.channel_states == [50, 75, 25]

    def test_set_channel_dimming_boundary_values(self):
        """Test setting channel dimming at boundary values"""
        assert self.xp33lr_service.set_channel_dimming(1, 0) is True
        assert self.xp33lr_service.set_channel_dimming(2, 100) is True

        assert self.xp33lr_service.channel_states[0] == 0
        assert self.xp33lr_service.channel_states[1] == 100

    def test_set_channel_dimming_invalid_channel(self):
        """Test setting dimming for invalid channel numbers"""
        assert self.xp33lr_service.set_channel_dimming(0, 50) is False
        assert self.xp33lr_service.set_channel_dimming(4, 50) is False
        assert self.xp33lr_service.set_channel_dimming(-1, 50) is False

    def test_set_channel_dimming_invalid_level(self):
        """Test setting invalid dimming levels"""
        assert self.xp33lr_service.set_channel_dimming(1, -10) is False
        assert self.xp33lr_service.set_channel_dimming(1, 150) is False

    def test_activate_scene_valid(self):
        """Test activating valid scenes"""
        assert self.xp33lr_service.activate_scene(1) is True
        assert self.xp33lr_service.channel_states == [50, 30, 20]

        assert self.xp33lr_service.activate_scene(2) is True
        assert self.xp33lr_service.channel_states == [100, 100, 100]

        assert self.xp33lr_service.activate_scene(4) is True
        assert self.xp33lr_service.channel_states == [0, 0, 0]

    def test_activate_scene_invalid(self):
        """Test activating invalid scene numbers"""
        assert self.xp33lr_service.activate_scene(0) is False
        assert self.xp33lr_service.activate_scene(5) is False
        assert self.xp33lr_service.activate_scene(-1) is False

    def test_process_system_telegram_discover(self):
        """Test processing discover system telegram"""
        request = SystemTelegram(
            checksum="FA",
            raw_telegram="<S0000000000F01D00FA>",
            serial_number="0000000000",
            system_function=SystemFunction.DISCOVERY,
            datapoint_type=DataPointType.MODULE_TYPE,
        )

        response = self.xp33lr_service.process_system_telegram(request)

        assert response == "<R0012345003F01DFD>"

    def test_process_system_telegram_wrong_serial(self):
        """Test processing telegram for wrong serial number"""
        request = SystemTelegram(
            checksum="FN",
            raw_telegram="<S1234567890F02D02FN>",
            serial_number="1234567890",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.SW_VERSION,
        )

        response = self.xp33lr_service.process_system_telegram(request)

        assert response is None

    def test_process_system_telegram_version_request(self):
        """Test processing version request"""
        request = SystemTelegram(
            checksum="FN",
            raw_telegram="<S0012345003F02D02FN>",
            serial_number="0012345003",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.SW_VERSION,
        )

        response = self.xp33lr_service.process_system_telegram(request)

        assert response == "<R0012345003F02D02XP33LR_V0.00.00HN>"

    def test_get_device_info(self):
        """Test getting device information"""
        info = self.xp33lr_service.get_device_info()

        expected_keys = [
            "serial_number",
            "device_type",
            "variant",
            "firmware_version",
            "ean_code",
            "max_power",
            "status",
            "link_number",
            "channel_states",
            "available_scenes",
        ]

        for key in expected_keys:
            assert key in info

        assert info["serial_number"] == "0012345003"
        assert info["device_type"] == "XP33"
        assert info["variant"] == "XP33LR"
        assert info["available_scenes"] == [1, 2, 3, 4]

    def test_get_technical_specs_xp33lr(self):
        """Test getting technical specifications for XP33LR"""
        specs = self.xp33lr_service.get_technical_specs()

        expected_keys = [
            "power_per_channel",
            "total_power",
            "load_types",
            "dimming_type",
            "protection",
        ]

        for key in expected_keys:
            assert key in specs

        assert specs["total_power"] == "640VA"
        assert specs["power_per_channel"] == "500VA max"
        assert "Resistive" in specs["load_types"]
        assert "inductive" in specs["load_types"]
        assert "Leading edge" in specs["dimming_type"]

    def test_get_technical_specs_xp33led(self):
        """Test getting technical specifications for XP33LED"""
        specs = self.xp33led_service.get_technical_specs()

        assert specs["total_power"] == "300VA"
        assert specs["power_per_channel"] == "100VA"
        assert "LED lamps" in specs["load_types"]
        assert "Leading/Trailing edge" in specs["dimming_type"]
        assert "Short-circuit proof" in specs["protection"]

    def test_channel_states_with_different_levels(self):
        """Test channel states response with different dimming levels"""
        # Set different levels
        self.xp33lr_service.set_channel_dimming(1, 50)  # 0x32
        self.xp33lr_service.set_channel_dimming(2, 75)  # 0x4B
        self.xp33lr_service.set_channel_dimming(3, 25)  # 0x19

        request = SystemTelegram(
            checksum="FM",
            raw_telegram="<S0012345003F02D12FM>",
            serial_number="0012345003",
            system_function=SystemFunction.READ_DATAPOINT,
            datapoint_type=DataPointType.MODULE_OUTPUT_STATE,
        )

        response = self.xp33lr_service.generate_channel_states_response(request)

        assert response == "<R0012345003F02D12324B19000BM>"
        assert "324B19000" in response  # 50%, 75%, 25% + padding

    def test_scene_configuration(self):
        """Test scene configuration and activation"""
        # Check default scene configuration
        assert self.xp33lr_service.scenes[1] == [50, 30, 20]
        assert self.xp33lr_service.scenes[2] == [100, 100, 100]
        assert self.xp33lr_service.scenes[3] == [25, 25, 25]
        assert self.xp33lr_service.scenes[4] == [0, 0, 0]

        # Test scene activation changes channel states
        original_states = self.xp33lr_service.channel_states.copy()
        self.xp33lr_service.activate_scene(3)
        assert self.xp33lr_service.channel_states == [25, 25, 25]
        assert self.xp33lr_service.channel_states != original_states

    def test_integration_with_telegram_service(self):
        """Test integration with TelegramService parsing"""
        # Test parsing and processing a real telegram
        raw_telegram = "<S0012345003F02D02FN>"
        parsed = self.telegram_service.parse_system_telegram(raw_telegram)

        assert parsed is not None
        response = self.xp33lr_service.process_system_telegram(parsed)

        assert response is not None
        assert response == "<R0012345003F02D02XP33LR_V0.00.00HN>"

        # Verify response can be parsed as reply telegram
        reply = self.telegram_service.parse_reply_telegram(response)
        assert reply is not None
        assert reply.serial_number == "0012345003"

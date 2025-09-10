import pytest
import tempfile
import os
import yaml
from src.xp.services.conbus_server_service import ConbusServerService
from src.xp.services.xp33_server_service import XP33ServerService
from src.xp.services.telegram_service import TelegramService


class TestXP33Integration:
    """Integration tests for XP33 emulator functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.telegram_service = TelegramService()
        
        # Create temporary config file
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yml')
        config_data = {
            'devices': {
                '0020042796': 'XP33LR',
                '0020042797': 'XP33LED',
                '2410010001': 'XP24'
            }
        }
        yaml.dump(config_data, self.temp_config)
        self.temp_config.close()
        
        # Create server with temporary config
        self.server = ConbusServerService(config_path=self.temp_config.name)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        if hasattr(self, 'temp_config'):
            os.unlink(self.temp_config.name)
    
    def test_server_loads_xp33_devices(self):
        """Test that server properly loads XP33 devices from config"""
        assert '0020042796' in self.server.devices
        assert '0020042797' in self.server.devices
        assert self.server.devices['0020042796'] == 'XP33LR'
        assert self.server.devices['0020042797'] == 'XP33LED'
    
    def test_server_creates_xp33_services(self):
        """Test that server creates XP33 service instances"""
        assert '0020042796' in self.server.device_services
        assert '0020042797' in self.server.device_services
        
        xp33lr_service = self.server.device_services['0020042796']
        xp33led_service = self.server.device_services['0020042797']
        
        assert isinstance(xp33lr_service, XP33ServerService)
        assert isinstance(xp33led_service, XP33ServerService)
        assert xp33lr_service.variant == 'XP33LR'
        assert xp33led_service.variant == 'XP33LED'
    
    def test_discovery_request_includes_xp33_devices(self):
        """Test that discovery requests include XP33 device responses"""
        discovery_request = '<S0000000000F01D00FA>'
        responses = self.server._process_request(discovery_request)
        
        # Filter out empty responses
        valid_responses = [r.strip() for r in responses if r.strip()]
        
        # Should have responses from XP33LR, XP33LED, and XP24
        assert len(valid_responses) >= 3
        
        # Check for specific XP33 responses
        xp33lr_response = None
        xp33led_response = None
        
        for response in valid_responses:
            if '0020042796' in response:
                xp33lr_response = response
            elif '0020042797' in response:
                xp33led_response = response
        
        assert xp33lr_response == '<R0020042796F01DFN>'
        assert xp33led_response == '<R0020042797F01DFM>'
    
    def test_xp33_version_request_processing(self):
        """Test processing version requests for XP33 devices"""
        # Test XP33LR version request
        lr_version_request = '<S0020042796F02D02FN>'
        lr_responses = self.server._process_request(lr_version_request)
        lr_response = lr_responses[0].strip() if lr_responses else None
        
        assert lr_response == '<R0020042796F02D02XP33LR_V0.04.02HF>'
        
        # Test XP33LED version request  
        led_version_request = '<S0020042797F02D02FN>'
        led_responses = self.server._process_request(led_version_request)
        led_response = led_responses[0].strip() if led_responses else None
        
        assert led_response is not None
        assert 'XP33LED_V0.04.02' in led_response
    
    def test_xp33_module_type_request_processing(self):
        """Test processing module type requests for XP33 devices"""
        module_type_request = '<S0020042796F02D07FI>'
        responses = self.server._process_request(module_type_request)
        response = responses[0].strip() if responses else None
        
        assert response == '<R0020042796F02D0730FK>'
        assert 'F02D07' in response
        assert '30' in response  # XP33 code 11 + offset = 48 = 0x30
    
    def test_xp33_status_query_processing(self):
        """Test processing status query requests for XP33 devices"""
        status_request = '<S0020042796F02D10FO>'
        responses = self.server._process_request(status_request)
        response = responses[0].strip() if responses else None
        
        assert response == '<R0020042796F02D1000FP>'
        assert 'F02D10' in response
        assert '00' in response  # Normal status
    
    def test_xp33_channel_states_processing(self):
        """Test processing channel states requests for XP33 devices"""
        channel_request = '<S0020042796F02D12FM>'
        responses = self.server._process_request(channel_request)
        response = responses[0].strip() if responses else None
        
        assert response == '<R0020042796F02D12000000000GN>'
        assert 'F02D12' in response
        assert '00000000' in response  # All channels at 0%
    
    def test_xp33_link_number_processing(self):
        """Test processing link number requests for XP33 devices"""
        link_request = '<S0020042796F02D04FL>'
        responses = self.server._process_request(link_request)
        response = responses[0].strip() if responses else None
        
        assert response == '<R0020042796F02D0404FO>'
        assert 'F02D04' in response
        assert '04' in response  # 4 links configured
    
    def test_xp33_individual_channel_processing(self):
        """Test processing individual channel control requests"""
        # Test channel 1 request
        ch1_request = '<S0020042796F02D13FN>'
        ch1_responses = self.server._process_request(ch1_request)
        ch1_response = ch1_responses[0].strip() if ch1_responses else None
        
        assert ch1_response is not None
        assert 'F02D13' in ch1_response
        assert '00000000' in ch1_response  # All channels at 0%
        
        # Test channel 2 request
        ch2_request = '<S0020042796F02D14FM>'
        ch2_responses = self.server._process_request(ch2_request)
        ch2_response = ch2_responses[0].strip() if ch2_responses else None
        
        assert ch2_response is not None
        assert 'F02D14' in ch2_response
        
        # Test channel 3 request
        ch3_request = '<S0020042796F02D15FL>'
        ch3_responses = self.server._process_request(ch3_request)
        ch3_response = ch3_responses[0].strip() if ch3_responses else None
        
        assert ch3_response is not None
        assert 'F02D15' in ch3_response
    
    def test_xp33_broadcast_requests(self):
        """Test broadcast requests to all devices"""
        # Test version broadcast
        version_broadcast = '<S0000000000F02D02FN>'
        responses = self.server._process_request(version_broadcast)
        valid_responses = [r.strip() for r in responses if r.strip()]
        
        # Should get responses from all devices (XP33LR, XP33LED, XP24)
        assert len(valid_responses) >= 3
        
        # Check that XP33 devices responded
        xp33_responses = [r for r in valid_responses if ('0020042796' in r or '0020042797' in r)]
        assert len(xp33_responses) >= 2
    
    def test_xp33_wrong_serial_no_response(self):
        """Test that XP33 devices don't respond to wrong serial numbers"""
        wrong_serial_request = '<S1234567890F02D02FN>'
        responses = self.server._process_request(wrong_serial_request)
        valid_responses = [r.strip() for r in responses if r.strip()]
        
        # Should get no responses for unknown serial number
        assert len(valid_responses) == 0
    
    def test_complete_xp33_workflow(self):
        """Test complete workflow with XP33 device"""
        xp33lr_service = self.server.device_services['0020042796']
        
        # 1. Discovery
        discovery_responses = self.server._process_request('<S0000000000F01D00FA>')
        discovery_valid = [r.strip() for r in discovery_responses if r.strip() and '0020042796' in r]
        assert len(discovery_valid) == 1
        assert discovery_valid[0] == '<R0020042796F01DFN>'
        
        # 2. Get version
        version_responses = self.server._process_request('<S0020042796F02D02FN>')
        version_response = version_responses[0].strip() if version_responses else None
        assert 'XP33LR_V0.04.02' in version_response
        
        # 3. Get module type
        module_responses = self.server._process_request('<S0020042796F02D07FI>')
        module_response = module_responses[0].strip() if module_responses else None
        assert '30' in module_response  # XP33 module type
        
        # 4. Get status
        status_responses = self.server._process_request('<S0020042796F02D10FO>')
        status_response = status_responses[0].strip() if status_responses else None
        assert '00' in status_response  # Normal status
        
        # 5. Get channel states (initial)
        channel_responses = self.server._process_request('<S0020042796F02D12FM>')
        initial_channel_response = channel_responses[0].strip() if channel_responses else None
        assert '00000000' in initial_channel_response  # All off
        
        # 6. Modify channel states directly (simulating control)
        xp33lr_service.set_channel_dimming(1, 50)
        xp33lr_service.set_channel_dimming(2, 75)
        xp33lr_service.set_channel_dimming(3, 25)
        
        # 7. Get channel states (after modification)
        channel_responses_2 = self.server._process_request('<S0020042796F02D12FM>')
        modified_channel_response = channel_responses_2[0].strip() if channel_responses_2 else None
        assert '324B1900' in modified_channel_response  # 50%, 75%, 25%
        
        # 8. Activate scene
        xp33lr_service.activate_scene(4)  # All off scene
        
        # 9. Verify scene activation
        channel_responses_3 = self.server._process_request('<S0020042796F02D12FM>')
        scene_channel_response = channel_responses_3[0].strip() if channel_responses_3 else None
        assert '00000000' in scene_channel_response  # Back to all off
    
    def test_xp33_device_info_integration(self):
        """Test device information integration"""
        xp33lr_service = self.server.device_services['0020042796']
        xp33led_service = self.server.device_services['0020042797']
        
        # Test XP33LR device info
        lr_info = xp33lr_service.get_device_info()
        assert lr_info['serial_number'] == '0020042796'
        assert lr_info['variant'] == 'XP33LR'
        assert lr_info['max_power'] == 640
        assert lr_info['ean_code'] == '5703513058982'
        
        # Test XP33LED device info
        led_info = xp33led_service.get_device_info()
        assert led_info['serial_number'] == '0020042797'
        assert led_info['variant'] == 'XP33LED'
        assert led_info['max_power'] == 300
        assert led_info['ean_code'] == '5703513058999'
    
    def test_xp33_technical_specs_integration(self):
        """Test technical specifications integration"""
        xp33lr_service = self.server.device_services['0020042796']
        xp33led_service = self.server.device_services['0020042797']
        
        # Test XP33LR specs
        lr_specs = xp33lr_service.get_technical_specs()
        assert lr_specs['total_power'] == '640VA'
        assert 'Resistive' in lr_specs['load_types']
        assert 'inductive' in lr_specs['load_types']
        
        # Test XP33LED specs
        led_specs = xp33led_service.get_technical_specs()
        assert led_specs['total_power'] == '300VA'
        assert 'LED lamps' in led_specs['load_types']
        assert 'Leading/Trailing edge' in led_specs['dimming_type']
    
    def test_mixed_device_types(self):
        """Test server handling mixed device types (XP24, XP33LR, XP33LED)"""
        # Discovery should return all devices
        discovery_responses = self.server._process_request('<S0000000000F01D00FA>')
        valid_responses = [r.strip() for r in discovery_responses if r.strip()]
        
        # Should have at least 3 devices (XP24, XP33LR, XP33LED)
        assert len(valid_responses) >= 3
        
        # Verify each device type responds correctly
        device_serials = ['2410010001', '0020042796', '0020042797']
        for serial in device_serials:
            device_responses = [r for r in valid_responses if serial in r]
            assert len(device_responses) == 1
            assert f'<R{serial}F01D' in device_responses[0]
    
    def test_config_reload_functionality(self):
        """Test configuration reload with XP33 devices"""
        # Initial state
        assert len(self.server.device_services) == 3
        
        # Update config file
        new_config_data = {
            'devices': {
                '0020042796': 'XP33LR',
                '0020042798': 'XP33LED',  # Different serial
            }
        }
        
        with open(self.temp_config.name, 'w') as f:
            yaml.dump(new_config_data, f)
        
        # Reload configuration
        self.server.reload_config()
        
        # Verify new configuration
        assert '0020042796' in self.server.device_services
        assert '0020042798' in self.server.device_services
        assert '0020042797' not in self.server.device_services  # Old one removed
        assert '2410010001' not in self.server.device_services  # XP24 removed
        
        # Test that new device works
        new_device_service = self.server.device_services['0020042798']
        assert new_device_service.variant == 'XP33LED'
        assert new_device_service.serial_number == '0020042798'
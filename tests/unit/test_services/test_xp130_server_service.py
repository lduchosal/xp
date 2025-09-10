import pytest
from src.xp.services.xp130_server_service import XP130ServerService, XP130ServerError
from src.xp.models.system_telegram import SystemTelegram, SystemFunction, DataPointType
from src.xp.services.telegram_service import TelegramService


class TestXP130ServerService:
    """Test cases for XP130ServerService"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.service = XP130ServerService('0019664896')
        self.telegram_service = TelegramService()
    
    def test_init(self):
        """Test XP130ServerService initialization"""
        service = XP130ServerService('0019664896')
        
        assert service.serial_number == '0019664896'
        assert service.device_type == 'XP130'
        assert service.firmware_version == 'XP130_V1.02.15'
        assert service.device_status == 'OK'
        assert service.link_number == 1
        assert service.ip_address == '192.168.1.100'
        assert service.subnet_mask == '255.255.255.0'
        assert service.gateway == '192.168.1.1'
    
    def test_generate_discovery_response(self):
        """Test discovery response generation"""
        response = self.service.generate_discovery_response()
        
        # Should generate <R{serial}F01D{checksum}>
        assert response.startswith('<R0019664896F01D')
        assert response.endswith('>')
        assert len(response) == 19  # <R + 10 digits + F01D + 2 char checksum + >
    
    def test_generate_version_response(self):
        """Test version response generation"""
        request = SystemTelegram(
            serial_number='0019664896',
            system_function=SystemFunction.RETURN_DATA,
            data_point_id=DataPointType.VERSION,
            checksum='FM',
            raw_telegram='<S0019664896F02D02FM>'
        )
        
        response = self.service.generate_version_response(request)
        
        assert response is not None
        assert 'XP130_V1.02.15' in response
        assert response.startswith('<R0019664896F02D02')
        assert response.endswith('>')
    
    def test_generate_version_response_wrong_request(self):
        """Test version response with wrong request type"""
        request = SystemTelegram(
            serial_number='0019664896',
            system_function=SystemFunction.RETURN_DATA,
            data_point_id=DataPointType.STATUS,
            checksum='FM',
            raw_telegram='<S0019664896F02D00FM>'
        )
        
        response = self.service.generate_version_response(request)
        assert response is None
    
    def test_generate_status_response(self):
        """Test status response generation"""
        request = SystemTelegram(
            serial_number='0019664896',
            system_function=SystemFunction.RETURN_DATA,
            data_point_id=DataPointType.STATUS,
            checksum='FM',
            raw_telegram='<S0019664896F02D00FM>'
        )
        
        response = self.service.generate_status_response(request)
        
        assert response is not None
        assert 'OK' in response
        assert response.startswith('<R0019664896F02D00')
        assert response.endswith('>')
    
    def test_generate_link_number_response(self):
        """Test link number response generation"""
        request = SystemTelegram(
            serial_number='0019664896',
            system_function=SystemFunction.RETURN_DATA,
            data_point_id=DataPointType.LINK_NUMBER,
            checksum='FO',
            raw_telegram='<S0019664896F02D04FO>'
        )
        
        response = self.service.generate_link_number_response(request)
        
        assert response is not None
        assert response.startswith('<R0019664896F02D04')
        assert response.endswith('>')
        # Should contain hex representation of link number (01)
        assert '01' in response
    
    def test_generate_ip_config_response(self):
        """Test IP configuration response generation"""
        request = SystemTelegram(
            serial_number='0019664896',
            system_function=SystemFunction.RETURN_DATA,
            data_point_id=DataPointType.NETWORK_CONFIG,
            checksum='GH',
            raw_telegram='<S0019664896F02D20GH>'
        )
        
        response = self.service.generate_ip_config_response(request)
        
        assert response is not None
        assert '192.168.1.100,255.255.255.0,192.168.1.1' in response
        assert response.startswith('<R0019664896F02D20')
        assert response.endswith('>')
    
    def test_generate_temperature_response(self):
        """Test temperature response generation"""
        request = SystemTelegram(
            serial_number='0019664896',
            system_function=SystemFunction.RETURN_DATA,
            data_point_id=DataPointType.TEMPERATURE,
            checksum='FN',
            raw_telegram='<S0019664896F02D18FN>'
        )
        
        response = self.service.generate_temperature_response(request)
        
        assert response is not None
        assert '+21,0§C' in response
        assert response.startswith('<R0019664896F02D18')
        assert response.endswith('>')
    
    def test_set_link_number(self):
        """Test setting link number"""
        request = SystemTelegram(
            serial_number='0019664896',
            system_function=SystemFunction.WRITE_CONFIG,
            data_point_id=DataPointType.LINK_NUMBER,
            checksum='FO',
            raw_telegram='<S0019664896F04D04FO>'
        )
        
        response = self.service.set_link_number(request, 5)
        
        assert response is not None
        assert self.service.link_number == 5
        assert response.startswith('<R0019664896F18D')
        assert response.endswith('>')
    
    def test_process_system_telegram_discovery(self):
        """Test processing discovery request"""
        request = SystemTelegram(
            serial_number='0019664896',
            system_function=SystemFunction.DISCOVERY,
            checksum='FG',
            raw_telegram='<S0019664896F01DFG>'
        )
        
        response = self.service.process_system_telegram(request)
        
        assert response is not None
        assert response.startswith('<R0019664896F01D')
        assert response.endswith('>')
    
    def test_process_system_telegram_wrong_serial(self):
        """Test processing request for wrong serial number"""
        request = SystemTelegram(
            serial_number='9999999999',
            system_function=SystemFunction.DISCOVERY,
            checksum='FG',
            raw_telegram='<S9999999999F01DFG>'
        )
        
        response = self.service.process_system_telegram(request)
        assert response is None
    
    def test_process_system_telegram_broadcast(self):
        """Test processing broadcast request"""
        request = SystemTelegram(
            serial_number='0000000000',
            system_function=SystemFunction.DISCOVERY,
            checksum='FG',
            raw_telegram='<S0000000000F01DFG>'
        )
        
        response = self.service.process_system_telegram(request)
        
        assert response is not None
        assert response.startswith('<R0019664896F01D')
        assert response.endswith('>')
    
    def test_get_device_info(self):
        """Test getting device information"""
        info = self.service.get_device_info()
        
        expected_info = {
            'serial_number': '0019664896',
            'device_type': 'XP130',
            'firmware_version': 'XP130_V1.02.15',
            'status': 'OK',
            'link_number': 1,
            'ip_address': '192.168.1.100',
            'subnet_mask': '255.255.255.0',
            'gateway': '192.168.1.1'
        }
        
        assert info == expected_info
import pytest
from src.xp.services.xp20_server_service import XP20ServerService, XP20ServerError
from src.xp.models.system_telegram import SystemTelegram, SystemFunction, DataPointType
from src.xp.services.telegram_service import TelegramService


class TestXP20ServerService:
    """Test cases for XP20ServerService"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.xp20_service = XP20ServerService('0020037487')
        self.telegram_service = TelegramService()
    
    def test_init(self):
        """Test XP20ServerService initialization"""
        service = XP20ServerService('0020037487')
        
        assert service.serial_number == '0020037487'
        assert service.device_type == 'XP20'
        assert service.firmware_version == 'XP20_V0.01.05'
        assert service.device_status == 'OK'
        assert service.link_number == 1
        assert service.module_type_code == 33  # XP20 code
    
    def test_generate_discovery_response(self):
        """Test discovery response generation"""
        response = self.xp20_service.generate_discovery_response()
        
        assert response == '<R0020037487F01DFJ>'
        assert response.startswith('<R0020037487F01D')
        assert response.endswith('>')
    
    def test_generate_module_type_response(self):
        """Test module type response generation"""
        request = SystemTelegram(
            checksum='FJ',
            raw_telegram='<S0020037487F02D07FJ>',
            serial_number='0020037487',
            system_function=SystemFunction.RETURN_DATA,
            data_point_id=DataPointType.MODULE_TYPE
        )
        
        response = self.xp20_service.generate_module_type_response(request)
        
        # XP20 should map to hex 33 according to spec
        expected_response = '<R0020037487F02D0721FL>'
        assert response == expected_response
        assert 'F02D07' in response
        assert '21' in response  # XP20 code is 33 = 0x21
    
    def test_generate_module_type_response_wrong_function(self):
        """Test module type response with wrong function returns None"""
        request = SystemTelegram(
            checksum='FJ',
            raw_telegram='<S0020037487F01D07FJ>',
            serial_number='0020037487',
            system_function=SystemFunction.DISCOVERY,  # Wrong function
            data_point_id=DataPointType.MODULE_TYPE
        )
        
        response = self.xp20_service.generate_module_type_response(request)
        assert response is None
    
    def test_process_system_telegram_module_type(self):
        """Test processing module type query through main handler"""
        request = SystemTelegram(
            checksum='FJ',
            raw_telegram='<S0020037487F02D07FJ>',
            serial_number='0020037487',
            system_function=SystemFunction.RETURN_DATA,
            data_point_id=DataPointType.MODULE_TYPE
        )
        
        response = self.xp20_service.process_system_telegram(request)
        
        expected_response = '<R0020037487F02D0721FL>'
        assert response == expected_response
        assert 'F02D07' in response
        assert '21' in response
    
    def test_process_system_telegram_broadcast(self):
        """Test processing telegram with broadcast serial"""
        request = SystemTelegram(
            checksum='FJ',
            raw_telegram='<S0000000000F02D07FJ>',
            serial_number='0000000000',  # Broadcast
            system_function=SystemFunction.RETURN_DATA,
            data_point_id=DataPointType.MODULE_TYPE
        )
        
        response = self.xp20_service.process_system_telegram(request)
        
        expected_response = '<R0020037487F02D0721FL>'
        assert response == expected_response
        assert 'F02D07' in response
        assert '21' in response
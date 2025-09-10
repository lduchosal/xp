from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List


class ModuleTypeCode(Enum):
    """Enum representing all XP system module type codes"""
    NOMOD = 0       # No module
    ALLMOD = 1      # Code matching every moduletype
    CP20 = 2        # CP switch link module
    CP70A = 3       # CP 38kHz IR link module
    CP70B = 4       # CP B&O IR link module
    CP70C = 5       # CP UHF link module
    CP70D = 6       # CP timer link module
    XP24 = 7        # XP relay module
    XP31UNI = 8     # XP universal load light dimmer
    XP31BC = 9      # XP ballast controller, 0-10VActions
    XP31DD = 10     # XP ballast controller DSI/DALI
    XP33 = 11       # XP 33 3 channel lightdimmer
    CP485 = 12      # CP RS485 interface module
    XP130 = 13      # Ethernet/TCPIP interface module
    XP2606 = 14     # 5 way push button panel with sesam, L-Team design
    XP2606A = 15    # 5 way push button panel with sesam, L-Team design and 38kHz IR receiver
    XP2606B = 16    # 5 way push button panel with sesam, L-Team design and B&O IR receiver
    XP26X1 = 17     # Reserved
    XP26X2 = 18     # Reserved
    XP2506 = 19     # 5 way push button panel with sesam, Conson design
    XP2506A = 20    # 5 way push button panel with sesam and 38kHz IR, Conson design
    XP2506B = 21    # 5 way push button panel with sesam and B&O IR, Conson design
    XPX1_8 = 22     # 8 way push button panel interface
    XP134 = 23      # Junctionbox interlink
    XP230 = 24      # XP230 module


@dataclass
class ModuleType:
    """
    Represents a module type in the XP system.
    Contains the module code, name, and description.
    """
    code: int
    name: str
    description: str
    
    @classmethod
    def from_code(cls, code: int) -> Optional['ModuleType']:
        """
        Create ModuleType from a numeric code.
        
        Args:
            code: The numeric module type code
            
        Returns:
            ModuleType instance or None if code is invalid
        """
        module_info = MODULE_TYPE_REGISTRY.get(code)
        if module_info:
            return cls(code=code, **module_info)
        return None
    
    @classmethod
    def from_name(cls, name: str) -> Optional['ModuleType']:
        """
        Create ModuleType from a module name.
        
        Args:
            name: The module name (case-insensitive)
            
        Returns:
            ModuleType instance or None if name is invalid
        """
        name_upper = name.upper()
        for code, info in MODULE_TYPE_REGISTRY.items():
            if info['name'].upper() == name_upper:
                return cls(code=code, **info)
        return None
    
    @property
    def is_reserved(self) -> bool:
        """Check if this module type is reserved"""
        return self.name in ['XP26X1', 'XP26X2']
    
    @property
    def is_push_button_panel(self) -> bool:
        """Check if this module type is a push button panel"""
        return self.name in ['XP2606', 'XP2606A', 'XP2606B', 'XP2506', 'XP2506A', 'XP2506B', 'XPX1_8']
    
    @property
    def is_ir_capable(self) -> bool:
        """Check if this module type has IR capabilities"""
        return any(ir_type in self.name for ir_type in ['38kHz', 'B&O']) or \
               any(ir_code in self.name for ir_code in ['CP70A', 'CP70B', 'XP2606A', 'XP2606B', 'XP2506A', 'XP2506B'])
    
    @property
    def category(self) -> str:
        """Get the module category based on its type"""
        if self.code <= 1:
            return "System"
        elif 2 <= self.code <= 6:
            return "CP Link Modules"
        elif 7 <= self.code <= 13:
            return "XP Control Modules"
        elif 14 <= self.code <= 24:
            return "Interface Panels"
        else:
            return "Unknown"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "is_reserved": self.is_reserved,
            "is_push_button_panel": self.is_push_button_panel,
            "is_ir_capable": self.is_ir_capable
        }
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        return f"{self.name} (Code {self.code}): {self.description}"


# Registry mapping module codes to their information
MODULE_TYPE_REGISTRY: Dict[int, Dict[str, str]] = {
    0: {"name": "NOMOD", "description": "No module"},
    1: {"name": "ALLMOD", "description": "Code matching every moduletype"},
    2: {"name": "CP20", "description": "CP switch link module"},
    3: {"name": "CP70A", "description": "CP 38kHz IR link module"},
    4: {"name": "CP70B", "description": "CP B&O IR link module"},
    5: {"name": "CP70C", "description": "CP UHF link module"},
    6: {"name": "CP70D", "description": "CP timer link module"},
    7: {"name": "XP24", "description": "XP relay module"},
    8: {"name": "XP31UNI", "description": "XP universal load light dimmer"},
    9: {"name": "XP31BC", "description": "XP ballast controller, 0-10VActions"},
    10: {"name": "XP31DD", "description": "XP ballast controller DSI/DALI"},
    11: {"name": "XP33", "description": "XP 33 3 channel lightdimmer"},
    12: {"name": "CP485", "description": "CP RS485 interface module"},
    13: {"name": "XP130", "description": "Ethernet/TCPIP interface module"},
    14: {"name": "XP2606", "description": "5 way push button panel with sesam, L-Team design"},
    15: {"name": "XP2606A", "description": "5 way push button panel with sesam, L-Team design and 38kHz IR receiver"},
    16: {"name": "XP2606B", "description": "5 way push button panel with sesam, L-Team design and B&O IR receiver"},
    17: {"name": "XP26X1", "description": "Reserved"},
    18: {"name": "XP26X2", "description": "Reserved"},
    19: {"name": "XP2506", "description": "5 way push button panel with sesam, Conson design"},
    20: {"name": "XP2506A", "description": "5 way push button panel with sesam and 38kHz IR, Conson design"},
    21: {"name": "XP2506B", "description": "5 way push button panel with sesam and B&O IR, Conson design"},
    22: {"name": "XPX1_8", "description": "8 way push button panel interface"},
    23: {"name": "XP134", "description": "Junctionbox interlink"},
    24: {"name": "XP230", "description": "XP230 module"},
}


def get_all_module_types() -> List[ModuleType]:
    """Get all available module types"""
    return [ModuleType.from_code(code) for code in sorted(MODULE_TYPE_REGISTRY.keys())]


def get_module_types_by_category() -> Dict[str, List[ModuleType]]:
    """Get module types grouped by category"""
    categories = {}
    for module_type in get_all_module_types():
        category = module_type.category
        if category not in categories:
            categories[category] = []
        categories[category].append(module_type)
    return categories


def is_valid_module_code(code: int) -> bool:
    """Check if a module code is valid"""
    return code in MODULE_TYPE_REGISTRY
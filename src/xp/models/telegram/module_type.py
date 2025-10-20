"""Module type models for the XP system."""

from dataclasses import dataclass
from typing import Dict, List, Optional

from xp.models.telegram.module_type_code import MODULE_TYPE_REGISTRY


@dataclass
class ModuleType:
    """Represents a module type in the XP system.

    Contains the module code, name, and description.

    Attributes:
        code: Numeric module type code.
        name: Module name.
        description: Module description.
        module_category: Module category.
        is_reserved: True if module type is reserved.
        is_push_button_panel: True if module is a push button panel.
        is_ir_capable: True if module has IR capabilities.
        category: Module category based on its type.
    """

    code: int
    name: str
    description: str
    module_category: str = ""

    @classmethod
    def from_code(cls, code: int) -> Optional["ModuleType"]:
        """Create ModuleType from a numeric code.

        Args:
            code: The numeric module type code.

        Returns:
            ModuleType instance or None if code is invalid.
        """
        module_info = MODULE_TYPE_REGISTRY.get(code)
        if module_info:
            return cls(code=code, **module_info)
        return None

    @classmethod
    def from_name(cls, name: str) -> Optional["ModuleType"]:
        """Create ModuleType from a module name.

        Args:
            name: The module name (case-insensitive).

        Returns:
            ModuleType instance or None if name is invalid.
        """
        name_upper = name.upper()
        for code, info in MODULE_TYPE_REGISTRY.items():
            if info["name"].upper() == name_upper:
                return cls(code=code, **info)
        return None

    @property
    def is_reserved(self) -> bool:
        """Check if this module type is reserved.

        Returns:
            True if module type is reserved, False otherwise.
        """
        return self.name in ("XP26X1", "XP26X2")

    @property
    def is_push_button_panel(self) -> bool:
        """Check if this module type is a push button panel.

        Returns:
            True if module is a push button panel, False otherwise.
        """
        return self.name in (
            "XP2606",
            "XP2606A",
            "XP2606B",
            "XP2506",
            "XP2506A",
            "XP2506B",
            "XPX1_8",
        )

    @property
    def is_ir_capable(self) -> bool:
        """Check if this module type has IR capabilities.

        Returns:
            True if module has IR capabilities, False otherwise.
        """
        return any(ir_type in self.name for ir_type in ("38kHz", "B&O")) or any(
            ir_code in self.name
            for ir_code in (
                "CP70A",
                "CP70B",
                "XP2606A",
                "XP2606B",
                "XP2506A",
                "XP2506B",
            )
        )

    @property
    def category(self) -> str:
        """Get the module category based on its type.

        Returns:
            Module category string.
        """
        if self.code <= 1:
            return "System"
        elif 2 <= self.code <= 6:
            return "CP Link Modules"
        elif 7 <= self.code <= 13:
            return "XP Control Modules"
        elif 14 <= self.code <= 24:
            return "Interface Panels"
        return "Unknown"

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the module type.
        """
        return {
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "is_reserved": self.is_reserved,
            "is_push_button_panel": self.is_push_button_panel,
            "is_ir_capable": self.is_ir_capable,
        }

    def __str__(self) -> str:
        """Return human-readable string representation.

        Returns:
            Formatted string representation.
        """
        return f"{self.name} (Code {self.code}): {self.description}"


def get_all_module_types() -> List[ModuleType]:
    """Get all available module types.

    Returns:
        List of all ModuleType instances.
    """
    return [
        module_type
        for module_type in [
            ModuleType.from_code(code) for code in sorted(MODULE_TYPE_REGISTRY.keys())
        ]
        if module_type is not None
    ]


def get_module_types_by_category() -> Dict[str, List[ModuleType]]:
    """Get module types grouped by category.

    Returns:
        Dictionary mapping category names to lists of ModuleType instances.
    """
    categories: Dict[str, List[ModuleType]] = {}
    for module_type in get_all_module_types():
        category = module_type.category
        if category not in categories:
            categories[category] = []
        categories[category].append(module_type)
    return categories


def is_valid_module_code(code: int) -> bool:
    """Check if a module code is valid.

    Args:
        code: Module code to validate.

    Returns:
        True if code is valid, False otherwise.
    """
    return code in MODULE_TYPE_REGISTRY

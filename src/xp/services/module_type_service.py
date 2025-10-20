"""Module Type Service for XP module management.

This module provides lookup, validation, and search functionality for XP system module types.
"""

from typing import Dict, List, Optional, Union

from xp.models.telegram.module_type import (
    ModuleType,
    get_all_module_types,
    get_module_types_by_category,
    is_valid_module_code,
)


class ModuleTypeNotFoundError(Exception):
    """Raised when a module type cannot be found."""

    pass


class ModuleTypeService:
    """
    Service for managing module type operations.

    Provides lookup, validation, and search functionality for XP system module types.
    """

    def __init__(self) -> None:
        """Initialize the module type service."""
        pass

    @staticmethod
    def get_module_type(identifier: Union[int, str]) -> ModuleType:
        """
        Get module type by code or name.

        Args:
            identifier: Module code (int) or name (str)

        Returns:
            ModuleType instance

        Raises:
            ModuleTypeNotFoundError: If module type is not found
        """
        if isinstance(identifier, int):
            module_type = ModuleType.from_code(identifier)
            if not module_type:
                raise ModuleTypeNotFoundError(
                    f"Module type with code {identifier} not found"
                )
        elif isinstance(identifier, str):
            module_type = ModuleType.from_name(identifier)
            if not module_type:
                raise ModuleTypeNotFoundError(
                    f"Module type with name '{identifier}' not found"
                )
        else:
            raise ModuleTypeNotFoundError(
                f"Invalid identifier type: {type(identifier)}"
            )

        return module_type

    @staticmethod
    def list_all_modules() -> List[ModuleType]:
        """
        Get all available module types.

        Returns:
            List of all ModuleType instances
        """
        return get_all_module_types()

    @staticmethod
    def list_modules_by_category() -> Dict[str, List[ModuleType]]:
        """
        Get module types grouped by category.

        Returns:
            Dictionary with category names as keys and lists of ModuleType as values
        """
        return get_module_types_by_category()

    @staticmethod
    def search_modules(
        query: str, search_fields: Optional[List[str]] = None
    ) -> List[ModuleType]:
        """
        Search for module types matching a query string.

        Args:
            query: Search query string
            search_fields: Fields to search in ('name', 'description'). Defaults to both.

        Returns:
            List of matching ModuleType instances
        """
        if search_fields is None:
            search_fields = ["name", "description"]

        query_lower = query.lower()
        matching_modules = []

        for module_type in get_all_module_types():
            match_found = False

            if "name" in search_fields and query_lower in module_type.name.lower():
                match_found = True
            elif (
                "description" in search_fields
                and query_lower in module_type.description.lower()
            ):
                match_found = True

            if match_found:
                matching_modules.append(module_type)

        return matching_modules

    @staticmethod
    def get_modules_by_category(category: str) -> List[ModuleType]:
        """
        Get all module types in a specific category.

        Args:
            category: Category name

        Returns:
            List of ModuleType instances in the category
        """
        return get_module_types_by_category().get(category, [])

    @staticmethod
    def get_push_button_panels() -> List[ModuleType]:
        """
        Get all push button panel module types.

        Returns:
            List of push button panel ModuleType instances
        """
        return [
            module for module in get_all_module_types() if module.is_push_button_panel
        ]

    @staticmethod
    def get_ir_capable_modules() -> List[ModuleType]:
        """
        Get all IR-capable module types.

        Returns:
            List of IR-capable ModuleType instances
        """
        return [module for module in get_all_module_types() if module.is_ir_capable]

    @staticmethod
    def validate_module_code(code: int) -> bool:
        """
        Validate if a module code is valid.

        Args:
            code: Module type code to validate

        Returns:
            True if valid, False otherwise
        """
        return is_valid_module_code(code)

    def get_module_info_summary(self, identifier: Union[int, str]) -> str:
        """
        Get a human-readable summary of a module type.

        Args:
            identifier: Module code (int) or name (str)

        Returns:
            Formatted string with module information
        """
        try:
            module_type = self.get_module_type(identifier)
            return self._format_module_summary(module_type)
        except ModuleTypeNotFoundError as e:
            return f"Error: {e}"

    def get_all_modules_summary(self, group_by_category: bool = False) -> str:
        """
        Get a formatted summary of all module types.

        Args:
            group_by_category: Whether to group modules by category

        Returns:
            Formatted string with all module information
        """
        if group_by_category:
            return self._format_modules_by_category()
        return self._format_all_modules()

    @staticmethod
    def _format_module_summary(module_type: ModuleType) -> str:
        """Format a single module type for display.

        Args:
            module_type: The module type to format.

        Returns:
            Formatted string with module information.
        """
        summary = f"Module: {module_type.name} (Code {module_type.code})\n"
        summary += f"Description: {module_type.description}\n"
        summary += f"Category: {module_type.category}\n"

        features = []
        if module_type.is_push_button_panel:
            features.append("Push Button Panel")
        if module_type.is_ir_capable:
            features.append("IR Capable")
        if module_type.is_reserved:
            features.append("Reserved")

        if features:
            summary += f"Features: {', '.join(features)}\n"

        return summary.strip()

    @staticmethod
    def _format_all_modules() -> str:
        """Format all modules in a simple list.

        Returns:
            Formatted string with all modules.
        """
        modules = get_all_module_types()
        lines = ["Code | Name       | Description", "-" * 60]

        for module in modules:
            lines.append(f"{module.code:4} | {module.name:10} | {module.description}")

        return "\n".join(lines)

    @staticmethod
    def _format_modules_by_category() -> str:
        """Format modules grouped by category.

        Returns:
            Formatted string with modules grouped by category.
        """
        categories = get_module_types_by_category()
        lines = []

        for category, modules in categories.items():
            lines.append(f"\n=== {category} ===")
            for module in modules:
                lines.append(f"  {module.code:2} - {module.name}: {module.description}")

        return "\n".join(lines).strip()

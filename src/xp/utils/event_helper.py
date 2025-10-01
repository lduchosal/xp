"""Event handling utilities for PyDispatcher integration.

This module provides clean, reusable utilities for handling PyDispatcher
responses across all HomeKit accessory classes.
"""

from typing import Any, Callable, List, Tuple


def get_first_response(
    responses: List[Tuple[Callable, Any]], default: Any = None
) -> Any:
    """Extract the first non-None response from PyDispatcher responses.

    Args:
        responses: List of (receiver_function, return_value) tuples from dispatcher.send()
        default: Value to return if no valid responses found

    Returns:
        First non-None response value, or default if none found

    Examples:
        >>> responses = [(<func1>, None), (<func2>, True), (<func3>, False)]
        >>> get_first_response(responses)
        True

        >>> responses = [(<func1>, None), (<func2>, None)]
        >>> get_first_response(responses, default=False)
        False
    """
    return next((r[1] for r in responses if r[1] is not None), default)

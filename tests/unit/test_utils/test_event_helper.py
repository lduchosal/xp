# Copyright (c) 2025 ldvchosal
"""Tests for event helper utilities."""

from typing import TYPE_CHECKING, Any

from xp.utils.event_helper import get_first_response

if TYPE_CHECKING:
    from collections.abc import Callable


class TestGetFirstResponse:
    """Test get_first_response function."""

    def test_returns_first_non_none_response(self) -> None:
        """Test function returns first non-None response."""

        def func1() -> None:
            """Test helper function."""

        def func2() -> None:
            """Test helper function."""

        def func3() -> None:
            """Test helper function."""

        responses = [(func1, None), (func2, True), (func3, False)]
        result = get_first_response(responses)
        assert result is True

    def test_returns_default_when_all_none(self) -> None:
        """Test function returns default when all responses are None."""

        def func1() -> None:
            """Test helper function."""

        def func2() -> None:
            """Test helper function."""

        responses: list[tuple[Callable[[], None], bool | None]] = [
            (func1, None),
            (func2, None),
        ]
        result = get_first_response(responses, default=False)
        assert result is False

    def test_returns_none_default_when_all_none(self) -> None:
        """Test function returns None by default when all responses are None."""

        def func1() -> None:
            """Test helper function."""

        responses = [(func1, None)]
        result = get_first_response(responses)
        assert result is None

    def test_returns_first_even_if_false(self) -> None:
        """Test function returns first non-None even if it's False."""

        def func1() -> None:
            """Test helper function."""

        def func2() -> None:
            """Test helper function."""

        responses = [(func1, False), (func2, True)]
        result = get_first_response(responses)
        assert result is False

    def test_returns_first_even_if_zero(self) -> None:
        """Test function returns first non-None even if it's 0."""

        def func1() -> None:
            """Test helper function."""

        def func2() -> None:
            """Test helper function."""

        responses = [(func1, 0), (func2, 100)]
        result = get_first_response(responses)
        assert result == 0

    def test_empty_responses_list(self) -> None:
        """Test function with empty responses list."""
        responses: list[tuple[Callable[..., Any], Any]] = []
        result = get_first_response(responses, default="default_value")
        assert result == "default_value"

    def test_complex_return_values(self) -> None:
        """Test function with complex return values."""

        def func1() -> None:
            """Test helper function."""

        def func2() -> None:
            """Test helper function."""

        def func3() -> None:
            """Test helper function."""

        responses = [(func1, None), (func2, {"key": "value"}), (func3, [1, 2, 3])]
        result = get_first_response(responses)
        assert result == {"key": "value"}

    def test_string_responses(self) -> None:
        """Test function with string responses."""

        def func1() -> None:
            """Test helper function."""

        def func2() -> None:
            """Test helper function."""

        responses = [(func1, None), (func2, "response_string")]
        result = get_first_response(responses)
        assert result == "response_string"

    def test_empty_string_is_returned(self) -> None:
        """Test empty string is considered a valid (non-None) response."""

        def func1() -> None:
            """Test helper function."""

        def func2() -> None:
            """Test helper function."""

        responses = [(func1, ""), (func2, "non-empty")]
        result = get_first_response(responses)
        # L'objet du test : "" est une réponse valide, distincte de None.
        assert result is not None
        assert not result

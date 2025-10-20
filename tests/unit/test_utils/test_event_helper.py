"""Tests for event helper utilities."""

from xp.utils.event_helper import get_first_response


class TestGetFirstResponse:
    """Test get_first_response function."""

    def test_returns_first_non_none_response(self):
        """Test function returns first non-None response."""

        def func1():
            """Test helper function."""
            pass

        def func2():
            """Test helper function."""
            pass

        def func3():
            """Test helper function."""
            pass

        responses = [(func1, None), (func2, True), (func3, False)]
        result = get_first_response(responses)
        assert result is True

    def test_returns_default_when_all_none(self):
        """Test function returns default when all responses are None."""

        def func1():
            """Test helper function."""
            pass

        def func2():
            """Test helper function."""
            pass

        responses = [(func1, None), (func2, None)]
        result = get_first_response(responses, default=False)
        assert result is False

    def test_returns_none_default_when_all_none(self):
        """Test function returns None by default when all responses are None."""

        def func1():
            """Test helper function."""
            pass

        responses = [(func1, None)]
        result = get_first_response(responses)
        assert result is None

    def test_returns_first_even_if_false(self):
        """Test function returns first non-None even if it's False."""

        def func1():
            """Test helper function."""
            pass

        def func2():
            """Test helper function."""
            pass

        responses = [(func1, False), (func2, True)]
        result = get_first_response(responses)
        assert result is False

    def test_returns_first_even_if_zero(self):
        """Test function returns first non-None even if it's 0."""

        def func1():
            """Test helper function."""
            pass

        def func2():
            """Test helper function."""
            pass

        responses = [(func1, 0), (func2, 100)]
        result = get_first_response(responses)
        assert result == 0

    def test_empty_responses_list(self):
        """Test function with empty responses list."""
        from typing import Any, Callable

        responses: list[tuple[Callable[..., Any], Any]] = []
        result = get_first_response(responses, default="default_value")
        assert result == "default_value"

    def test_complex_return_values(self):
        """Test function with complex return values."""

        def func1():
            """Test helper function."""
            pass

        def func2():
            """Test helper function."""
            pass

        def func3():
            """Test helper function."""
            pass

        responses = [(func1, None), (func2, {"key": "value"}), (func3, [1, 2, 3])]
        result = get_first_response(responses)
        assert result == {"key": "value"}

    def test_string_responses(self):
        """Test function with string responses."""

        def func1():
            """Test helper function."""
            pass

        def func2():
            """Test helper function."""
            pass

        responses = [(func1, None), (func2, "response_string")]
        result = get_first_response(responses)
        assert result == "response_string"

    def test_empty_string_is_returned(self):
        """Test empty string is considered a valid (non-None) response."""

        def func1():
            """Test helper function."""
            pass

        def func2():
            """Test helper function."""
            pass

        responses = [(func1, ""), (func2, "non-empty")]
        result = get_first_response(responses)
        assert result == ""

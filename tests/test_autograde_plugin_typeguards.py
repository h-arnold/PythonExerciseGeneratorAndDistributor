"""Unit tests for autograde_plugin type guards.

These tests verify that the type guards correctly identify valid and invalid
inputs, ensuring both runtime correctness and proper type narrowing for static
analysis.
"""

from __future__ import annotations

from tests.autograde_plugin_typeguards import is_marker_args, is_marker_kwargs


class TestIsMarkerKwargs:
    """Tests for is_marker_kwargs type guard."""

    def test_accepts_empty_dict(self):
        """Empty dict is valid marker kwargs."""
        assert is_marker_kwargs({}) is True

    def test_accepts_dict_with_string_keys(self):
        """Dict with string keys is valid marker kwargs."""
        assert is_marker_kwargs({"task": 1, "name": "test"}) is True

    def test_accepts_dict_with_any_values(self):
        """Dict with any value types is valid marker kwargs."""
        assert is_marker_kwargs({"a": 1, "b": "str", "c": None, "d": [1, 2, 3]}) is True

    def test_rejects_none(self):
        """None is not valid marker kwargs."""
        assert is_marker_kwargs(None) is False

    def test_rejects_list(self):
        """List is not valid marker kwargs."""
        assert is_marker_kwargs([1, 2, 3]) is False

    def test_rejects_tuple(self):
        """Tuple is not valid marker kwargs."""
        assert is_marker_kwargs((1, 2, 3)) is False

    def test_rejects_string(self):
        """String is not valid marker kwargs."""
        assert is_marker_kwargs("not a dict") is False

    def test_rejects_int(self):
        """Int is not valid marker kwargs."""
        assert is_marker_kwargs(42) is False


class TestIsMarkerArgs:
    """Tests for is_marker_args type guard."""

    def test_accepts_empty_tuple(self):
        """Empty tuple is valid marker args."""
        assert is_marker_args(()) is True

    def test_accepts_tuple_with_elements(self):
        """Tuple with elements is valid marker args."""
        assert is_marker_args((1, 2, 3)) is True

    def test_accepts_list(self):
        """List is valid marker args."""
        assert is_marker_args([1, 2, 3]) is True

    def test_accepts_empty_list(self):
        """Empty list is valid marker args."""
        assert is_marker_args([]) is True

    def test_accepts_range(self):
        """Range is valid marker args (it's a Sequence)."""
        assert is_marker_args(range(5)) is True

    def test_rejects_string(self):
        """String is a Sequence but should be rejected for marker args."""
        assert is_marker_args("not valid") is False

    def test_rejects_bytes(self):
        """Bytes is a Sequence but should be rejected for marker args."""
        assert is_marker_args(b"not valid") is False

    def test_rejects_none(self):
        """None is not valid marker args."""
        assert is_marker_args(None) is False

    def test_rejects_dict(self):
        """Dict is not a Sequence, so not valid marker args."""
        assert is_marker_args({"key": "value"}) is False

    def test_rejects_int(self):
        """Int is not a Sequence, so not valid marker args."""
        assert is_marker_args(42) is False

    def test_accepts_mixed_types_in_sequence(self):
        """Sequence with mixed types is valid marker args."""
        assert is_marker_args([1, "two", None, [3, 4]]) is True

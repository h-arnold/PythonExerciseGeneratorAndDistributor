"""Type guards for autograde_plugin.py.

Provides runtime type checking functions that narrow types for static analysis.
These guards are kept simple and focused on surface-level property checking.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, TypeGuard


def is_marker_kwargs(obj: object) -> TypeGuard[dict[str, Any]]:
    """Check if obj is a dict suitable for marker kwargs.

    Args:
        obj: The object to check.

    Returns:
        True if obj is a dict, False otherwise.
    """
    return isinstance(obj, dict)


def is_marker_args(obj: object) -> TypeGuard[Sequence[Any]]:
    """Check if obj is a Sequence suitable for marker args.

    Excludes str and bytes as they are sequences but not suitable for marker args.

    Args:
        obj: The object to check.

    Returns:
        True if obj is a Sequence but not str or bytes, False otherwise.
    """
    return isinstance(obj, Sequence) and not isinstance(obj, (str, bytes))

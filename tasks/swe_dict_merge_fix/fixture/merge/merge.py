from __future__ import annotations

from typing import Any, Dict


def merge_dicts(base: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    """Return a merged dictionary of base and patch."""

    if not isinstance(base, dict) or not isinstance(patch, dict):
        raise TypeError("Both base and patch must be dictionaries")

    result = dict(base)

    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value

    return result

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable

from core.grading import GradeResult
from core.json_io import EnvelopeParseError, parse_envelope

_TOLERANCE = 0.005  # 0.5%


def _normalize_results(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, Iterable):
        return []
    results = []
    for item in value:
        if not isinstance(item, dict):
            continue
        category = item.get("category")
        revenue = item.get("revenue")
        if isinstance(category, str) and isinstance(revenue, (int, float)):
            results.append({"category": category, "revenue": float(revenue)})
    return results


def _close(expected: float, actual: float) -> bool:
    if expected == 0:
        return abs(actual) <= 0.01
    return abs(actual - expected) / expected <= _TOLERANCE


def grade(envelope: Any, sandbox_path: Path, metadata: Dict[str, Any]) -> GradeResult:
    try:
        parsed = parse_envelope(envelope)
    except EnvelopeParseError as exc:
        return GradeResult(False, 0.0, {"error": str(exc)})

    answer = parsed.get("answer")
    if not isinstance(answer, dict):
        return GradeResult(False, 0.0, {"error": "answer must be an object"})

    submitted = _normalize_results(answer.get("results"))
    expected = metadata.get("expected", [])

    expected_map = {item["category"]: item["revenue"] for item in expected}
    submitted_map = {item["category"]: item["revenue"] for item in submitted}

    true_positive = sum(
        1
        for category, revenue in submitted_map.items()
        if category in expected_map and _close(expected_map[category], revenue)
    )
    precision = true_positive / len(submitted_map) if submitted_map else 0.0
    recall = true_positive / len(expected_map) if expected_map else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    all_match = (
        len(submitted_map) == len(expected_map)
        and all(category in expected_map and _close(expected_map[category], revenue) for category, revenue in submitted_map.items())
    )

    signals = {
        "expected": expected,
        "submitted": submitted,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "variant": metadata.get("variant"),
    }

    return GradeResult(all_match, f1, signals)


__all__ = ["grade"]

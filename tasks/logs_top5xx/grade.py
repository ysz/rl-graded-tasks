from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable

from core.grading import GradeResult
from core.json_io import EnvelopeParseError, parse_envelope


def _normalize_results(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, Iterable):
        return []
    results = []
    for item in value:
        if not isinstance(item, dict):
            continue
        ip = item.get("ip")
        count = item.get("count")
        if isinstance(ip, str) and isinstance(count, int):
            results.append({"ip": ip, "count": count})
    return results


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

    expected_map = {item["ip"]: item["count"] for item in expected}
    submitted_map = {item["ip"]: item["count"] for item in submitted}

    true_positive = sum(1 for ip, count in submitted_map.items() if expected_map.get(ip) == count)
    precision = true_positive / len(submitted_map) if submitted_map else 0.0
    recall = true_positive / len(expected_map) if expected_map else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    passed = submitted == expected

    signals = {
        "submitted": submitted,
        "expected": expected,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "variant": metadata.get("variant"),
    }

    return GradeResult(passed, f1, signals)


__all__ = ["grade"]

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

from core.grading import GradeResult
from core.json_io import EnvelopeParseError, parse_envelope


def _safe_paths(value: Any) -> List[str]:
    if not isinstance(value, Iterable):
        return []
    paths: List[str] = []
    for item in value:
        if isinstance(item, str):
            paths.append(item)
    return paths


def grade(envelope: Any, sandbox_path: Path, metadata: Dict[str, Any]) -> GradeResult:
    try:
        parsed = parse_envelope(envelope)
    except EnvelopeParseError as exc:
        return GradeResult(passed=False, reward=0.0, signals={"error": str(exc)})

    answer = parsed.get("answer", {})
    if not isinstance(answer, dict):
        return GradeResult(
            passed=False,
            reward=0.0,
            signals={"error": "Answer field must be an object"},
        )

    submitted_paths = _safe_paths(answer.get("paths"))
    expected = metadata.get("expected_paths", [])
    expected_set = set(expected)
    submitted_set = set(submitted_paths)

    true_positive = len(expected_set & submitted_set)
    precision = true_positive / len(submitted_set) if submitted_set else 0.0
    recall = true_positive / len(expected_set) if expected_set else 0.0
    if true_positive == 0 and not submitted_set and expected_set:
        f1 = 0.0
    elif true_positive == 0 and not expected_set:
        f1 = 1.0
    else:
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

    passed = submitted_paths == expected

    signals = {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "expected_paths": expected,
        "submitted_paths": submitted_paths,
        "variant": metadata.get("variant"),
        "sandbox": sandbox_path.name,
    }

    return GradeResult(passed=passed, reward=f1, signals=signals)


__all__ = ["grade"]

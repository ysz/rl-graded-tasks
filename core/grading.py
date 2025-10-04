from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(slots=True)
class GradeResult:
    """Container returned by graders."""

    passed: bool
    reward: float
    signals: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": bool(self.passed),
            "reward": float(self.reward),
            "signals": dict(self.signals),
        }


__all__ = ["GradeResult"]

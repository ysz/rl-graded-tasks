from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field


class Envelope(BaseModel):
    """Pydantic model representing the unified output envelope."""

    model_config = ConfigDict(extra="forbid")

    passed: bool = Field(description="Whether the task is considered passed by the agent")
    checks: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional per check diagnostics or partial scores",
    )
    answer: Any = Field(description="Task specific payload used by the grader")
    notes: str | None = Field(
        default=None,
        description="Optional free form message for humans",
    )


ENVELOPE_JSON_SCHEMA: Dict[str, Any] = Envelope.model_json_schema()

__all__ = ["Envelope", "ENVELOPE_JSON_SCHEMA"]
